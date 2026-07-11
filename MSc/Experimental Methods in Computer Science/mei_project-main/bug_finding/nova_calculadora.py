import pandas as pd
import numpy as np
from scipy import stats
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

import os

ALPHA = 0.1
P0 = 0.75
EXCEL_PATH = os.path.join(os.path.dirname(__file__), 'llms_analysis.xlsx')

# ─────────────────────────────────────────────
# 0. CARREGAR DADOS
# ─────────────────────────────────────────────
sheets = {'gemini': 'Gemini', 'chatgpt': 'ChatGPT', 'claude': 'Claude'}
dfs = []

for sheet, label in sheets.items():
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet)
    df = df[df['Case_ID'].notna() & (df['Case_ID'] != 'Médias')].copy()
    df['Model'] = label
    df['Difficulty'] = df['Difficulty'].replace({'Low': 'Easy'})
    dfs.append(df)

data = pd.concat(dfs, ignore_index=True)
data['Recall'] = pd.to_numeric(data['Recall'], errors='coerce')
data = data.dropna(subset=['Recall'])

models_all = ['Gemini', 'ChatGPT', 'Claude']

# ─────────────────────────────────────────────
# DESCRITIVAS INICIAIS
# ─────────────────────────────────────────────
print("=" * 65)
print("ANÁLISE INICIAL — TODOS OS MODELOS")
print("=" * 65)

for m in models_all:
    vals = data[data['Model'] == m]['Recall']
    print(f"{m:<10} n={len(vals)} mean={vals.mean():.4f}")

# ─────────────────────────────────────────────
# TWO-WAY ANOVA (COM OS 3 MODELOS)
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("TWO-WAY ANOVA (TODOS OS MODELOS)")
print("=" * 65)

models = models_all
difficulties = ['Easy', 'Medium', 'Hard']

a, b = len(models), len(difficulties)

cell_means, cell_vals = {}, {}

for m in models:
    for d in difficulties:
        vals = data[(data['Model'] == m) &
                    (data['Difficulty'] == d)]['Recall'].values
        cell_vals[(m, d)] = vals
        cell_means[(m, d)] = vals.mean() if len(vals) > 0 else np.nan

grand_mean = data['Recall'].mean()
N = len(data)

SS_A = sum(
    sum(len(cell_vals[(m, d)]) for d in difficulties) *
    (data[data['Model'] == m]['Recall'].mean() - grand_mean) ** 2
    for m in models
)

SS_B = sum(
    sum(len(cell_vals[(m, d)]) for m in models) *
    (data[data['Difficulty'] == d]['Recall'].mean() - grand_mean) ** 2
    for d in difficulties
)

SS_W = sum(
    sum((v - cell_means[(m, d)]) ** 2 for v in cell_vals[(m, d)])
    for m in models for d in difficulties
)

df_A = a - 1
df_B = b - 1
df_W = N - a - b

F_A = (SS_A / df_A) / (SS_W / df_W)
F_B = (SS_B / df_B) / (SS_W / df_W)

p_A = 1 - stats.f.cdf(F_A, df_A, df_W)
p_B = 1 - stats.f.cdf(F_B, df_B, df_W)

print(f"Modelo: F={F_A:.4f}, p={p_A:.4f}")
print(f"Dificuldade: F={F_B:.4f}, p={p_B:.4f}")

print("\nCONCLUSÃO — TWO-WAY ANOVA")
if p_A < ALPHA and p_B < ALPHA:
    print("✔ Existem diferenças significativas entre modelos E dificuldades.")
elif p_A < ALPHA:
    print("✔ Existem diferenças significativas entre modelos (não entre dificuldades).")
elif p_B < ALPHA:
    print("✔ A dificuldade influencia significativamente o recall (modelos não diferem).")
else:
    print("✖ Não há evidência estatística de diferenças entre modelos ou dificuldades.")

# ─────────────────────────────────────────────
# PASSO 2 — THRESHOLD (ELIMINAÇÃO)
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("PASSO 2 — THRESHOLD 75%")
print("=" * 65)

active_models = []

for m in models_all:
    vals = data[data['Model'] == m]['Recall'].values
    n = len(vals)
    p_hat = vals.mean()

    z = (p_hat - P0) / np.sqrt(P0 * (1 - P0) / n)
    pval = 1 - stats.norm.cdf(z)

    print(f"\n{m}: p̂={p_hat:.4f}, z={z:.4f}, p={pval:.4f}")

    if pval < ALPHA:
        active_models.append(m)
        print("✔ PASSA")
    else:
        print("✖ ELIMINADO")

print("\nMODELOS ATIVOS:", active_models)

# filtrar dados
data_active = data[data['Model'].isin(active_models)]
models = active_models

# ─────────────────────────────────────────────
# Z-TEST (SÓ MODELOS ATIVOS)
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("Z-TEST (MODELOS ATIVOS)")
print("=" * 65)

z_scores = {}

for m in models:
    vals = data_active[data_active['Model'] == m]['Recall'].values
    n = len(vals)
    p_hat = vals.mean()

    z = (p_hat - P0) / np.sqrt(P0 * (1 - P0) / n)
    z_scores[m] = z

    print(f"{m}: p̂={p_hat:.4f}, z={z:.4f}")

param_ranking = sorted(z_scores.keys(), key=lambda m: z_scores[m], reverse=True)


ALPHA = 0.01
# ─────────────────────────────────────────────
# KRUSKAL-WALLIS (ATIVOS)
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("KRUSKAL-WALLIS")
print("=" * 65)

groups = [data_active[data_active['Model'] == m]['Recall'] for m in models]

if len(models) >= 2:
    kw_stat, kw_p = stats.kruskal(*groups)
    print(f"H={kw_stat:.4f}, p={kw_p:.4f}")

    print("\nCONCLUSÃO — KRUSKAL-WALLIS")
    if kw_p < ALPHA:
        print("✔ Pelo menos um modelo tem distribuição de recall significativamente diferente.")
        print("  → Justifica comparação par-a-par (Mann–Whitney).")
    else:
        print("✖ Não há diferenças significativas entre os modelos ativos.")
        print("  → Comparações par-a-par têm pouca evidência estatística.")

# ─────────────────────────────────────────────
# MANN-WHITNEY (ATIVOS)
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("MANN-WHITNEY")
print("=" * 65)

wins = {m: 0 for m in models}

for m1, m2 in combinations(models, 2):
    x = data_active[data_active['Model'] == m1]['Recall']
    y = data_active[data_active['Model'] == m2]['Recall']

    stat, p = stats.mannwhitneyu(x, y, alternative='two-sided')

    winner = m1 if x.mean() > y.mean() else m2
    wins[winner] += 1

    print(f"{m1} vs {m2}: p={p:.4f} → {winner}")

nonparam_ranking = sorted(wins.keys(), key=lambda m: wins[m], reverse=True)

# ─────────────────────────────────────────────
# COMPARAÇÃO FINAL
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("COMPARAÇÃO DOS RANKINGS")
print("=" * 65)

print("\nRanking paramétrico (Z-test):")
for i, m in enumerate(param_ranking, 1):
    print(f"{i}. {m}")

print("\nRanking não paramétrico (Mann–Whitney):")
for i, m in enumerate(nonparam_ranking, 1):
    print(f"{i}. {m}")

if param_ranking == nonparam_ranking:
    print("\n✔ CONCLUSÃO: Rankings coincidem (robustez)")
else:
    print("\n⚠ CONCLUSÃO: Rankings diferem (sensibilidade ao método)")