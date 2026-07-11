import numpy as np
import math

chatgpt = [17.4, 17.7, 17.4, 17.4, 18.2, 17.4, 18.2, 18.2, 17.8, 18.2]
claude  = [16.2, 16.9, 18.5, 18.5, 16.8, 16.2, 16.7, 17.6, 18.9, 17.5]
gemini  = [15.8, 15.8, 16.2, 16.2, 17.5, 15.8, 15.9, 16.9, 17.2, 16.1]

modelos = {"ChatGPT": chatgpt, "Claude": claude, "Gemini": gemini}

for nome, notas in modelos.items():
    media = np.mean(notas)
    variancia = sum((x - media) ** 2 for x in notas) / (len(notas) - 1)
    dp = math.sqrt(variancia)
    print(f"{nome}: média = {media:.2f} | desvio padrão (s) = {dp:.3f}")