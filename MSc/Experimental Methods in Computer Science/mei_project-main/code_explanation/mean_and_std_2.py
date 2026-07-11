import numpy as np
import math

chatgpt = [17.4, 17.7, 17.4, 17.4, 18.2, 17.4, 18.2, 18.2, 17.8, 18.2, 19.1, 19.3, 18.9, 18.5, 17.2, 18.1, 19.6, 18.5, 17.8, 18.2]
claude  = [16.2, 16.9, 18.5, 18.5, 16.8, 16.2, 16.7, 17.6, 18.9, 17.5, 15.3, 13.8, 14.6, 16.5, 16.3, 15.5, 14.2, 16.4, 14.1, 14.6]


modelos = {"ChatGPT": chatgpt, "Claude": claude}

for nome, notas in modelos.items():
    media = np.mean(notas)
    variancia = sum((x - media) ** 2 for x in notas) / (len(notas) - 1)
    dp = math.sqrt(variancia)
    print(f"{nome}: média = {media:.2f} | desvio padrão (s) = {dp:.3f}")