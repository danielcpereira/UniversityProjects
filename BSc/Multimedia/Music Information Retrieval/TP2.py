import os
import librosa
import numpy as np
import scipy
import scipy.stats as stats
import pandas as pd

musicas = []
nomes = []
features = []
sc_librosa = []
sc_raiz = []

def carregar_musicas(caminho):

    ficheiros = os.listdir(caminho)
    ficheiros.sort()
    
    for ficheiro in ficheiros:
        musica = librosa.load(caminho+"\\"+ficheiro, sr = 22050, mono = True)
        musicas.append(musica)
        nomes.append(ficheiro)

def extrair_features(musicas):
    
    features_todas = []
    
    for musica in musicas:
        y, sr = musica
        
        # Features espectrais
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc = 13)
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
        sc_librosa.append(spectral_centroid)
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr)[:7, :]
        spectral_flatness = librosa.feature.spectral_flatness(y=y)
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
        
        # Features temporais
        rms = librosa.feature.rms(y=y)
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y=y)
        f0 = librosa.yin(y, fmin=22, fmax=sr/2)
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        tempo = librosa.feature.tempo(onset_envelope=onset_env, sr=sr)
        
        features_dict = {
            'mfcc': mfcc,
            'spectral_centroid': spectral_centroid,
            'spectral_bandwidth': spectral_bandwidth,
            'spectral_contrast': spectral_contrast,
            'spectral_flatness': spectral_flatness,
            'spectral_rolloff': spectral_rolloff,
            'rms': rms,
            'zero_crossing_rate': zero_crossing_rate,
            'f0': np.array([f0]),
            'tempo': tempo
        }
        
        features_todas.append(features_dict)
    
    return np.array(features_todas, dtype=object)

def calcular_estatisticas():

    num_musicas = len(features)
    array_estatisticas = np.zeros((num_musicas, 190))
    
    for i, feature_dict in enumerate(features):
        indice = 0
        
        for nome, valores in feature_dict.items():
            if nome == "tempo":
                array_estatisticas[i, indice] = valores[0]
                indice += 1
            elif nome == "mfcc" or nome == "spectral_contrast":
                for j in range(len(valores)):
                    feature = np.nan_to_num(valores[j])
                    array_estatisticas[i, indice:indice+7] = estatisticas(feature)
                    indice += 7
            else:
                feature = np.nan_to_num(valores[0])
                array_estatisticas[i, indice:indice+7] = estatisticas(feature)
                indice += 7
    
    return array_estatisticas

def estatisticas(feature):

    estatisticas = np.array([
                        np.mean(feature),
                        np.std(feature),
                        stats.skew(feature),
                        stats.kurtosis(feature),
                        np.median(feature),
                        np.max(feature),
                        np.min(feature)
                    ])

    return estatisticas

def normalizar_features(features_matrix):

    num_features = features_matrix.shape[1]
    features_norm = np.zeros_like(features_matrix, dtype=float)
    min_max = np.zeros((2, num_features))
    
    for i in range(num_features):
        min_max[0, i] = np.min(features_matrix[:, i])
        min_max[1, i] = np.max(features_matrix[:, i])
        
        if min_max[1, i] - min_max[0, i] != 0:
            features_norm[:, i] = (features_matrix[:, i] - min_max[0, i]) / (min_max[1, i] - min_max[0, i])
    
    matriz_norm = np.vstack((min_max, features_norm))
    
    return matriz_norm

def guardar_ficheiro(nome_ficheiro, matriz, formato):
    np.savetxt(nome_ficheiro, matriz, delimiter=",", fmt=formato)

def spectral_centroid_manual(window_size=2048, hop_size=512):
    sc_raiz_temp = []
    
    for musica in musicas:
        y, sr = musica
        
        possiveis_janelas = len(y) // hop_size

        num_janelas = max(0, possiveis_janelas - 3)

        tamanho_necessario = (num_janelas - 1) * hop_size + window_size if num_janelas > 0 else 0

        if len(y) < tamanho_necessario:
            padding = tamanho_necessario - len(y)
            y = np.pad(y, (0, padding), mode='constant')
        
        freqs = scipy.fft.rfftfreq(window_size, d=1/sr)
        sc_musica = np.zeros(num_janelas)
        
        for i in range(num_janelas):
            indice = i * hop_size
            window = y[indice:indice + window_size]
            spectrum = np.abs(scipy.fft.rfft(window * np.hanning(window_size)))
            
            if np.sum(spectrum) != 0:
                sc = np.sum(freqs * spectrum) / np.sum(spectrum)
                sc_musica[i] = sc
        
        sc_raiz_temp.append(sc_musica)
    
    global sc_raiz
    sc_raiz = np.array(sc_raiz_temp, dtype=object)

def metricas_erro():

    num_musicas = len(sc_librosa)
    metricas = np.zeros((num_musicas, 2))
    
    for i in range(num_musicas):
        raiz_atual = np.array(sc_raiz[i])
        librosa_atual = sc_librosa[i][0]
        
        if len(raiz_atual) > 2:
            raiz_atual = raiz_atual[:-2] 
        
        if len(librosa_atual) > 2:
            librosa_atual = librosa_atual[2:] 
        
        min_tam = min(len(raiz_atual), len(librosa_atual))
        
        if min_tam > 0:

            raiz_atual = raiz_atual[:min_tam]
            librosa_atual = librosa_atual[:min_tam]
            
            metricas[i, 0] = np.corrcoef(raiz_atual, librosa_atual)[0, 1]
            
            metricas[i, 1] = np.sqrt(np.mean((raiz_atual - librosa_atual) ** 2))
        else:
            metricas[i, 0] = 0
            metricas[i, 1] = 0
    
    return metricas

def calcular_distancia_euclidiana(vetor_query, vetor_features):
    return np.sqrt(np.sum((vetor_query - vetor_features)**2))

def calcular_distancia_manhattan(vetor_query, vetor_features):
    return np.sum(np.abs(vetor_query - vetor_features))

def calcular_distancia_coseno(vetor_query, vetor_features):
    
    return(
        1 - np.dot(vetor_query, vetor_features) / (np.linalg.norm(vetor_query) * np.linalg.norm(vetor_features)) 
        if np.linalg.norm(vetor_query) * np.linalg.norm(vetor_features) != 0 
        else 1.0 
    )

def processar_query(features_norm_path, caminho_query):
    
    matriz_norm = np.genfromtxt(features_norm_path, delimiter=",")

    musicas_query = []
    musica_query = librosa.load(caminho_query, sr=22050, mono=True)
    musicas_query.append(musica_query)
    
    global features
    features_query = extrair_features(musicas_query)    

    backup_features = features
    features = features_query
    estatisticas_query = calcular_estatisticas()
    features = backup_features
    
    min_max = matriz_norm[:2, :]
    features_norm = matriz_norm[2:, :]

    vetor_query = estatisticas_query[0]
    vetor_query_norm = np.zeros_like(vetor_query, dtype=float)
    
    for i in range(len(vetor_query)):
        min_val = min_max[0, i]
        max_val = min_max[1, i]
        
        if max_val - min_val != 0:
            vetor_query_norm[i] = (vetor_query[i] - min_val) / (max_val - min_val)
        else:
            vetor_query_norm[i] = 0.0
    
    return vetor_query, vetor_query_norm, features_norm

def calcular_similaridades(vetor_query_norm, features_norm):
     
    dist_euclidiana = np.zeros(len(features_norm))
    dist_manhattan = np.zeros(len(features_norm))
    dist_coseno = np.zeros(len(features_norm))   

    for i in range(len(musicas)):
        dist_euclidiana[i] = calcular_distancia_euclidiana(vetor_query_norm, features_norm[i])
        dist_manhattan[i] = calcular_distancia_manhattan(vetor_query_norm, features_norm[i])
        dist_coseno[i] = calcular_distancia_coseno(vetor_query_norm, features_norm[i])
            
    matrizes_similaridade = {
        'euclidiana': dist_euclidiana,
        'manhattan': dist_manhattan,
        'coseno': dist_coseno
    }
    
    return matrizes_similaridade

def ranking_similaridade(matrizes_similaridade, top_n=11):

    rankings = {}
    
    for nome_metrica, distancias in matrizes_similaridade.items():

        indices_ordenados = np.argsort(distancias)
        
        top_indices = indices_ordenados[:top_n]
        top_distancias = distancias[top_indices]
        
        top_nomes = [nomes[i] for i in top_indices]
        ranking = list(zip(top_nomes, top_distancias))
        
        rankings[nome_metrica] = ranking
    
    return rankings

def calcular_similaridade_metadados(md_query, md_dataset):
 
    if len(md_query) != 1:
        print("Erro: Deve haver apenas uma música query!")
        return None
    
    artista_query = str(md_query['Artist'].iloc[0]).lower().strip() if not pd.isna(md_query['Artist'].iloc[0]) else ""
    
    moods_query = set()
    if not pd.isna(md_query['MoodsStrSplit'].iloc[0]):
        moods_str = str(md_query['MoodsStrSplit'].iloc[0]).lower()

        if moods_str.strip():
            moods_query = set(mood.strip() for mood in moods_str.split(';') if mood.strip())
    
    generos_query = set()
    if not pd.isna(md_query['GenresStr'].iloc[0]):
        generos_str = str(md_query['GenresStr'].iloc[0]).lower()

        if generos_str.strip():
            generos_query = set(genero.strip() for genero in generos_str.split(';') if genero.strip())
    
    similaridade_metadata = np.zeros(len(md_dataset))
    
    for i, linha in md_dataset.iterrows():

        if not pd.isna(linha['Artist']):
            artista_alvo = str(linha['Artist']).lower().strip()
            if artista_query and artista_alvo and artista_query == artista_alvo:
                similaridade_metadata[i] += 1
        
        if not pd.isna(linha['MoodsStrSplit']) and moods_query:
            moods_str_alvo = str(linha['MoodsStrSplit']).lower()
            if moods_str_alvo.strip():
                moods_alvo = set(mood.strip() for mood in moods_str_alvo.split(';') if mood.strip())

                for mood in moods_query.intersection(moods_alvo):
                    similaridade_metadata[i] += 1
        
        if not pd.isna(linha['GenresStr']) and generos_query:
            generos_str_alvo = str(linha['GenresStr']).lower()
            if generos_str_alvo.strip():
                generos_alvo = set(genero.strip() for genero in generos_str_alvo.split(';') if genero.strip())

                for genero in generos_query.intersection(generos_alvo):
                    similaridade_metadata[i] += 1
    
    return similaridade_metadata

def criar_ranking_metadados(similaridade_metadata, top_n=11):
    
    indices_ordenados = np.argsort(-similaridade_metadata)

    top_indices = indices_ordenados[:top_n]
    top_similaridade_metadata = similaridade_metadata[top_indices]
    
    ranking = []
    for i, (idx, score) in enumerate(zip(top_indices, top_similaridade_metadata)):
        nome_musica = nomes[idx]
        ranking.append((i+1, nome_musica, idx, score))
    
    return indices_ordenados, ranking

def calcular_precision(ranking_metadados_indices, rankings, top_n=11):
   
    relevantes = set(ranking_metadados_indices[:top_n])
    
    precision_dict = {}
    
    for nome_metrica, ranking in rankings.items():

        indices = [nomes.index(nome) for nome, _ in ranking[1:top_n]]
        
        itens_relevantes = sum(1 for idx in indices if idx in relevantes)
        
        precision = (itens_relevantes / (top_n - 1)) * 100
        precision_dict[nome_metrica] = precision
    
    return precision_dict

def avaliacao_objetiva(rankings):

    caminho_query = "query_metadata.csv"
    caminho_dataset = "panda_dataset_taffc_metadata.csv"

    md_query = pd.read_csv(caminho_query)
    md_dataset = pd.read_csv(caminho_dataset)
    
    print("A calcular similaridade baseada em metadados...")
    similaridade_metadata = calcular_similaridade_metadados(md_query, md_dataset)
    guardar_ficheiro('similaridade_metadados.csv', similaridade_metadata, "%d")
    
    print("A calcular ranking metadados...")
    indices_ordenados, ranking_metadados = criar_ranking_metadados(similaridade_metadata)

    with open('rankings_precisao.txt', 'a') as f:
        f.write("\nRanking metadados:\n")
        for pos, nome_musica, idx, score in ranking_metadados:
            f.write(f"{pos}. {nome_musica} (Índice: {idx}): {score} pontos\n")
    
    
    print("A calcular precisão dos rankings acústicos...")
    precision = calcular_precision(indices_ordenados, rankings)

    with open('rankings_precisao.txt', 'a') as f:
        f.write("\nPrecisão dos rankings acústicos baseada em metadados:\n")
        for metrica, valor in precision.items():
            f.write(f"Precisão para distância {metrica}: {valor:.4f}\n")
    
    print("Avaliação objetiva concluída!")
    

def main():
    caminho = "MER_audio_taffc_dataset\\musicas"
    
    carregar_musicas(caminho)

    global features
    features = extrair_features(musicas) 
    print("Features extraídas com sucesso!")
    
    estatisticas = calcular_estatisticas()
    guardar_ficheiro('features.csv', estatisticas, "%.6f")
    
    matriz_norm = normalizar_features(estatisticas)
    guardar_ficheiro('features_norm.csv', matriz_norm, "%.6f")
    
    spectral_centroid_manual()
    metricas = metricas_erro()
    guardar_ficheiro('metricas_erro.csv', metricas, "%.6f")
    
    caminho_query = "Queries\\MT0000414517.mp3"
    print("A processar a query...")
    vetor_query, vetor_query_norm, features_norm = processar_query('features_norm.csv', caminho_query)
    guardar_ficheiro('query.csv', vetor_query, "%.6f")
    guardar_ficheiro('query_norm.csv', vetor_query_norm, "%.6f")
        
    matrizes_similaridade = calcular_similaridades(vetor_query_norm, features_norm)
    print("Matrizes de similaridade criadas")
    guardar_ficheiro('similaridade_euclidiana.csv', matrizes_similaridade['euclidiana'], "%.6f")
    guardar_ficheiro('similaridade_manhattan.csv', matrizes_similaridade['manhattan'], "%.6f")
    guardar_ficheiro('similaridade_coseno.csv', matrizes_similaridade['coseno'], "%.6f")

    rankings = ranking_similaridade(matrizes_similaridade)
    print("Rankings de similaridade criados com sucesso!")
    with open('rankings_precisao.txt', 'w') as f:
        for metrica, ranking in rankings.items():
            f.write(f"Ranking usando distância {metrica}:\n")
            for i, (nome_musica, dist) in enumerate(ranking):
                f.write(f"{i+1}. Música {nome_musica}: {dist:.6f}\n")
            f.write("\n")
    
    avaliacao_objetiva(rankings)

if __name__ == "__main__":
    main()