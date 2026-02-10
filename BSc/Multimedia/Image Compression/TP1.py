# ==============================================================
#                    Trabalho Prático 1
#                        Multimédia
# 
# 
#                          
# Daniel Coelho Pereira             Nº 2021237092
# Eduardo Luís Pereira Marques      Nº 2022231584
# Sérgio Lopes Marques              Nº 2022222096                      
# ==============================================================


import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as clr  
import cv2
from scipy.fftpack import dct, idct

rgb_to_ycbcr = np.array([
        [0.299, 0.587, 0.114],
        [-0.168736, -0.331264, 0.5],
        [0.5, -0.418688, -0.081312]
    ])

quality_factors = [10, 25, 50, 75, 100]

quantization_matrix_y = np.array([
        [16, 11, 10, 16, 24, 40, 51, 61],
        [12, 12, 14, 19, 26, 58, 60, 55],
        [14, 13, 16, 24, 40, 57, 69, 56],
        [14, 17, 22, 29, 51, 87, 80, 62],
        [18, 22, 37, 56, 68, 109, 103, 77],
        [24, 35, 55, 64, 81, 104, 113, 92],
        [49, 64, 78, 87, 103, 121, 120, 101],
        [72, 92, 95, 98, 112, 100, 103, 99]
    ])

quantization_matrix_cb_cr = np.array([
        [17, 18, 24, 47, 99, 99, 99, 99],
        [18, 21, 26, 66, 99, 99, 99, 99],
        [24, 26, 56, 99, 99, 99, 99, 99],
        [47, 66, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99],
        [99, 99, 99, 99, 99, 99, 99, 99]
])

def encoder(img, qf, size=32):
    
    img_padded = padding(img, size)
    
    R, G, B = separar_RGB(img_padded)
    
    y,cb,cr = RGB_to_YCbCr(R,G,B)
    
    y_d, cb_d, cr_d = down_sampling(y,cb,cr,(4, 2, 2))

    y_dct, cb_dct, cr_dct = apply_dct_to_channels(y_d, cb_d, cr_d)

    y_dct_blocks_8, cb_dct_blocks_8, cr_dct_blocks_8 = apply_dct_to_blocks(y_d, cb_d, cr_d, 8)

    y_dct_blocks_64, cb_dct_blocks_64, cr_dct_blocks_64 = apply_dct_to_blocks(y_d, cb_d, cr_d, 64)

    y_q, cb_q, cr_q = quantize_dct(y_dct_blocks_8, cb_dct_blocks_8, cr_dct_blocks_8, qf)

    y_dpcm, cb_dpcm, cr_dpcm = apply_dpcm(y_q, cb_q, cr_q) 

    return R, G, B, y, cb, cr, y_d, cb_d, cr_d, y_dct, cb_dct, cr_dct, y_dct_blocks_8, cb_dct_blocks_8, cr_dct_blocks_8, y_dct_blocks_64, cb_dct_blocks_64, cr_dct_blocks_64, y_q, cb_q, cr_q, y_dpcm, cb_dpcm, cr_dpcm, img_padded.shape


def decoder(y_dpcm, cb_dpcm, cr_dpcm, block_size, qf, original_shape):

    y_q, cb_q, cr_q = apply_idpcm(y_dpcm, cb_dpcm, cr_dpcm)

    y_dct, cb_dct, cr_dct = dequantize_dct(y_q, cb_q, cr_q, qf)

    if block_size == 0:
            y_d, cb_d, cr_d = apply_idct_to_channels(y_dct, cb_dct, cr_dct)
    else:
        y_d, cb_d, cr_d = apply_idct_to_blocks(y_dct, cb_dct, cr_dct, block_size)

    y, cb, cr = up_sampling(y_d,cb_d,cr_d)
    
    R,G,B = YCbCr_to_RGB(y,cb,cr)

    img_padded = juntar_RGB(R, G, B)

    return y, remove_padding(img_padded, original_shape)

def separar_RGB(img):

    R = img[:, :, 0]
    G = img[:, :, 1]  
    B = img[:, :, 2]  

    return R, G, B

def juntar_RGB(R, G, B):

    img = np.stack((R, G, B), axis=-1)

    return img

def padding(img, size=32):
    altura, largura, c = img.shape
    
    pad_altura = (size - (altura % size)) % size
    pad_largura = (size - (largura % size)) % size
    
    if pad_altura == 0 and pad_largura == 0:
        return img  
    
    if pad_altura > 0:
        last_row = img[-1:, :, :]
        padding_rows = np.vstack([last_row] * pad_altura)
        img = np.vstack((img, padding_rows))
    
    if pad_largura > 0:
        last_col = img[:, -1:, :]
        padding_cols = np.hstack([last_col] * pad_largura)
        img = np.hstack((img, padding_cols))
    
    return img

def remove_padding(img_padded, original_shape):
    h, w, _ = original_shape 
    return img_padded[:h, :w, :]

def showImg(cmap, img, title=" "):
    plt.figure()
    
    if cmap is None:
        plt.imshow(img, cmap = None)  
    else:
        plt.imshow(img, cmap=cmap)
        
    plt.axis('off')
    plt.title(title)
    plt.show()

def showImgDCT(cmap, img, title=" "):
    plt.figure()
    
    if cmap is None:
        plt.imshow(np.log(np.abs(img) + 0.0001), cmap = None)  
    else:
        plt.imshow(np.log(np.abs(img) + 0.0001), cmap=cmap)
        
    plt.axis('off')
    plt.title(title)
    plt.show()

def create_custom_colormap(name, key_colors, N=256):
    return clr.LinearSegmentedColormap.from_list(name, key_colors, N)


def RGB_to_YCbCr(R,G,B):
    
    y = 0.299 * R + 0.587 * G + 0.114 * B
    cb = ((B-y) / 1.772) + 128
    cr = ((R-y) / 1.402) + 128
   
    return  y,cb,cr


def YCbCr_to_RGB(y,cb,cr):
    matriz = get_inverse_YCbCr_matrix()

    y  = y
    cb = cb - 128
    cr = cr - 128

    R = matriz[0, 0] * y + matriz[0, 1] * cb + matriz[0, 2] * cr
    G = matriz[1, 0] * y + matriz[1, 1] * cb + matriz[1, 2] * cr
    B = matriz[2, 0] * y + matriz[2, 1] * cb + matriz[2, 2] * cr

    R = np.clip(R, 0, 255).astype(np.uint8)
    G = np.clip(G, 0, 255).astype(np.uint8)
    B = np.clip(B, 0, 255).astype(np.uint8)

    return R,G,B
    

def get_inverse_YCbCr_matrix():

    matriz = np.linalg.inv(rgb_to_ycbcr)

    return matriz


def down_sampling(y, cb, cr, sampling_factor,  interpolation=cv2.INTER_LINEAR):
    
    altura, largura = y.shape[:2]
    factor_y, factor_cb, factor_cr = sampling_factor
    
    y_d = y 
    
    
    if factor_cr != 4:
        if  factor_cb == 0:
            cr_d = cv2.resize(cr, (int(np.floor(largura * 0.5)), int(np.floor(altura * 0.5))), interpolation=interpolation)
        else:
            cr_d = cv2.resize(cr, (int(largura * (factor_cr / 4)), int(altura)), interpolation=interpolation)
    else:
        cr_d = cr
    
        
    if factor_cb != 4 :
        if  factor_cb == 0:
            cb_d = cv2.resize(cb, (int(np.floor(largura * 0.5)), int(np.floor(altura * 0.5))), interpolation=interpolation)
        else:   
            cb_d = cv2.resize(cb, (int(largura * (factor_cb / 4)), int(altura)), interpolation=interpolation)
    else: 
        cb_d = cb    
        
    return y_d, cb_d, cr_d
        
def up_sampling(y, cb, cr, interpolation=cv2.INTER_LINEAR):
    altura, largura = y.shape[:2]

    original_cb = cv2.resize(cb, (largura, altura), interpolation=interpolation)
    original_cr = cv2.resize(cr, (largura, altura), interpolation=interpolation)

    return y, original_cb, original_cr

def dct2(X):
    return dct(dct(X, norm='ortho').T, norm='ortho').T

def idct2(X):
    return idct(idct(X, norm='ortho').T, norm='ortho').T

def apply_dct_to_channels(y_d, cb_d, cr_d):
    y_dct = dct2(y_d)
    cb_dct = dct2(cb_d)
    cr_dct = dct2(cr_d)
    
    return y_dct, cb_dct, cr_dct

def apply_idct_to_channels(y_dct, cb_dct, cr_dct):
    y_idct = idct2(y_dct)
    cb_idct = idct2(cb_dct)
    cr_idct = idct2(cr_dct)

    return y_idct, cb_idct, cr_idct

def dct_blocks(X, block_size):
    altura, largura = X.shape[:2]
    X_dct_blocks = np.zeros_like(X)

    for i in range(0, altura, block_size):
        for j in range(0, largura, block_size):
            block = X[i:i+block_size, j:j+block_size]
            X_dct_blocks[i:i+block_size, j:j+block_size] = dct2(block)
    
    return X_dct_blocks

def idct_blocks(X_dct, block_size):
    altura, largura = X_dct.shape[:2]
    X_idct_blocks = np.zeros_like(X_dct)

    for i in range(0, altura, block_size):
        for j in range(0, largura, block_size):
            block_dct = X_dct[i:i+block_size, j:j+block_size]
            X_idct_blocks[i:i+block_size, j:j+block_size] = idct2(block_dct)
    
    return X_idct_blocks

def apply_dct_to_blocks(y_d, cb_d, cr_d, block_size):
    y_dct_blocks = dct_blocks(y_d, block_size)
    cb_dct_blocks = dct_blocks(cb_d, block_size)
    cr_dct_blocks = dct_blocks(cr_d, block_size)

    return y_dct_blocks, cb_dct_blocks, cr_dct_blocks

def apply_idct_to_blocks(y_dct_blocks, cb_dct_blocks, cr_dct_blocks, block_size):
    y_idct_blocks = idct_blocks(y_dct_blocks, block_size)
    cb_idct_blocks = idct_blocks(cb_dct_blocks, block_size)
    cr_idct_blocks = idct_blocks(cr_dct_blocks, block_size)

    return y_idct_blocks, cb_idct_blocks, cr_idct_blocks
    
def quantize_dct(y_dct_blocks_8, cb_dct_blocks_8, cr_dct_blocks_8, quality_factor):

    if quality_factor < 50:
        scale_factor = 50 / quality_factor
    else:
        scale_factor = (100 - quality_factor) / 50

    quantization_matrix_Y = np.clip(np.round(quantization_matrix_y * scale_factor), 1, 255).astype(np.uint8)
    quantization_matrix_CB_CR = np.clip(np.round(quantization_matrix_cb_cr * scale_factor), 1, 255).astype(np.uint8)

    altura_y, largura_y = y_dct_blocks_8.shape[:2]
    altura_cb, largura_cb = cb_dct_blocks_8.shape[:2]
    altura_cr, largura_cr = cr_dct_blocks_8.shape[:2]

    y_q = np.zeros_like(y_dct_blocks_8)
    cb_q = np.zeros_like(cb_dct_blocks_8)
    cr_q = np.zeros_like(cr_dct_blocks_8)

    for i in range(0, altura_y, 8):
        for j in range(0, largura_y, 8):
            y_q[i:i+8, j:j+8] = np.round(y_dct_blocks_8[i:i+8, j:j+8] / quantization_matrix_Y)
    
    for i in range(0, altura_cb, 8):
        for j in range(0, largura_cb, 8):
            cb_q[i:i+8, j:j+8] = np.round(cb_dct_blocks_8[i:i+8, j:j+8] / quantization_matrix_CB_CR)

    for i in range(0, altura_cr, 8):
        for j in range(0, largura_cr, 8):
            cr_q[i:i+8, j:j+8] = np.round(cr_dct_blocks_8[i:i+8, j:j+8] / quantization_matrix_CB_CR)

    return y_q, cb_q, cr_q

def dequantize_dct(y_q, cb_q, cr_q, quality_factor):
    
    if quality_factor < 50:
        scale_factor = 50 / quality_factor
    else:
        scale_factor = (100 - quality_factor) / 50

    quantization_matrix_Y = np.clip(np.round(quantization_matrix_y * scale_factor), 1, 255).astype(np.uint8)
    quantization_matrix_CB_CR = np.clip(np.round(quantization_matrix_cb_cr * scale_factor), 1, 255).astype(np.uint8)

    altura_y, largura_y = y_q.shape[:2]
    altura_cb, largura_cb = cb_q.shape[:2]
    altura_cr, largura_cr = cr_q.shape[:2]

    y_iq = np.zeros_like(y_q)
    cb_iq = np.zeros_like(cb_q)
    cr_iq = np.zeros_like(cr_q)

    for i in range(0, altura_y, 8):
        for j in range(0, largura_y, 8):
            y_iq[i:i+8, j:j+8] = np.round(y_q[i:i+8, j:j+8] * quantization_matrix_Y)
    
    for i in range(0, altura_cb, 8):
        for j in range(0, largura_cb, 8):
            cb_iq[i:i+8, j:j+8] = np.round(cb_q[i:i+8, j:j+8] * quantization_matrix_CB_CR)

    for i in range(0, altura_cr, 8):
        for j in range(0, largura_cr, 8):
            cr_iq[i:i+8, j:j+8] = np.round(cr_q[i:i+8, j:j+8] * quantization_matrix_CB_CR)

    return y_iq, cb_iq, cr_iq

def dpcm_encode(canal_q):
  
    altura, largura = canal_q.shape[:2]
    canal_dpcm = canal_q.copy()

    for i in range(0, altura, 8):
        for j in range(0, largura, 8):
            if j > 0:
                canal_dpcm[i:i + 8, j:j + 8][0, 0] -= canal_q[i:i + 8, j - 8:j][0, 0]
            elif i > 0:
                canal_dpcm[i:i+8, j:j + 8][0, 0] -= canal_q[i - 8:i, j:j + 8][0, 0]

    return canal_dpcm

def dpcm_decode(canal_dpcm):

    altura, largura = canal_dpcm.shape[:2]
    canal_idpcm = canal_dpcm.copy()

    for i in range(0, altura, 8):
        for j in range(0, largura, 8):
            if j > 0:
                canal_idpcm[i:i + 8, j:j + 8][0, 0] += canal_idpcm[i:i + 8, j - 8:j][0, 0]
            elif i > 0:
                canal_idpcm[i:i + 8, j:j + 8][0, 0] += canal_idpcm[i - 8:i, j:j + 8][0, 0]

    return canal_idpcm
   
def apply_dpcm(y_q, cb_q, cr_q):

    y_dpcm = dpcm_encode(y_q)
    cb_dpcm = dpcm_encode(cb_q)
    cr_dpcm = dpcm_encode(cr_q)

    return y_dpcm, cb_dpcm, cr_dpcm
    
def apply_idpcm(y_dpcm, cb_dpcm, cr_dpcm):

    y_idpcm = dpcm_decode(y_dpcm)
    cb_idpcm = dpcm_decode(cb_dpcm)
    cr_idpcm = dpcm_decode(cr_dpcm)
    
    return y_idpcm, cb_idpcm, cr_idpcm

def diff(original_channel, rebuilt_channel):

    difference = abs(original_channel - rebuilt_channel)
    
    print("MAX: ", np.max(difference))
    print("AVG: ", np.mean(difference))
    
    showImg("gray", difference,'Difference (Y)')
    
def distortion_metrics(img, img_rec):
        
    Io = img.astype(np.float32)
    Ir = img_rec.astype(np.float32)
    shape  = np.shape(img)

    MSE = np.sum((Io - Ir)**2)/(int(shape[0]) * int(shape[1]))
    RMSE = np.sqrt(MSE)
    
    P = np.sum(Io**2)/(int(shape[0]) * int(shape[1]))
    SNR = np.log10(P/MSE) * 10
    PSNR = np.log10(np.max(Io)**2 / MSE) * 10

    return MSE, RMSE, SNR, PSNR

def main():
    img = plt.imread("imagensBMP/airport.bmp")
    original_shape = img.shape 

    R, G, B, y, cb, cr, y_d, cb_d, cr_d, y_dct, cb_dct, cr_dct, y_dct_blocks_8, cb_dct_blocks_8, cr_dct_blocks_8, y_dct_blocks_64, cb_dct_blocks_64, cr_dct_blocks_64, y_q, cb_q, cr_q, y_dpcm, cb_dpcm, cr_dpcm, padded_shape = encoder(img, 1)

    color_map_red = create_custom_colormap("Vermelho", [(0, 0, 0), (1, 0, 0)])
    showImg(color_map_red, R, "Red")
    color_map_green = create_custom_colormap("Verde", [(0, 0, 0), (0, 1, 0)])
    showImg(color_map_green, G, "Green")
    color_map_blue = create_custom_colormap("Azul", [(0, 0, 0), (0, 0, 1)])
    showImg(color_map_blue, B, "Blue")
        
    showImg("gray", y, "Canal Y")
    showImg("gray", cb, "Canal Cb")
    showImg("gray", cr, "Canal Cr")
    
    showImg("gray", y_d, "Canal Y com downsampling")
    showImg("gray", cb_d, "Canal Cb com downsampling")
    showImg("gray", cr_d, "Canal Cr com downsampling")

    showImgDCT("gray", y_dct, "Canal Y com DCT")
    showImgDCT("gray", cb_dct, "Canal Cb com DCT")
    showImgDCT("gray", cr_dct, "Canal Cr com DCT")

    showImgDCT("gray", y_dct_blocks_8, "Canal Y com DCT em blocos 8x8")
    showImgDCT("gray", cb_dct_blocks_8, "Canal Cb com DCT em blocos 8x8")
    showImgDCT("gray", cr_dct_blocks_8, "Canal Cr com DCT em blocos 8x8")

    showImgDCT("gray", y_dct_blocks_64, "Canal Y com DCT em blocos 64x64")
    showImgDCT("gray", cb_dct_blocks_64, "Canal Cb com DCT em blocos 64x64")
    showImgDCT("gray", cr_dct_blocks_64, "Canal Cr com DCT em blocos 64x64")

    for qf in quality_factors:

        R, G, B, y, cb, cr, y_d, cb_d, cr_d, y_dct, cb_dct, cr_dct, y_dct_blocks_8, cb_dct_blocks_8, cr_dct_blocks_8, y_dct_blocks_64, cb_dct_blocks_64, cr_dct_blocks_64, y_q, cb_q, cr_q, y_dpcm, cb_dpcm, cr_dpcm, padded_shape = encoder(img, qf)

        showImgDCT("gray", y_q, f"Canal Y Quantizado (QF={qf})")
        showImgDCT("gray", cb_q, f"Canal Cb Quantizado (QF={qf})")
        showImgDCT("gray", cr_q, f"Canal Cr Quantizado (QF={qf})")

        showImgDCT("gray", y_dpcm, "Canal Y com DPCM")
        showImgDCT("gray", cb_dpcm, "Canal Cb com DPCM")
        showImgDCT("gray", cr_dpcm, "Canal Cr com DPCM")

        y_rec, img_recovered = decoder(y_dpcm, cb_dpcm, cr_dpcm, 8, qf, original_shape)
        showImg(None, img_recovered, "Imagem Reconstruída")

        diff(y, y_rec)

        MSE, RMSE, SNR, PSNR = distortion_metrics(img, img_recovered)

        print("MSE: ", MSE)
        print("RMSE: ", RMSE)
        print("SNR: ", SNR)
        print("PSNR: ", PSNR)

if __name__ == "__main__":
    main()