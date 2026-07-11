import pandas as pd
import numpy as np
from scipy import stats
from itertools import combinations
import warnings
warnings.filterwarnings('ignore')

import os

ALPHA = 0.1  # nível de significância
P0 = 0.75  # threshold Passo 2
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

print("=" * 65)
print("       ANÁLISE ESTATÍSTICA — RECALL DOS 3 LLMs")
print("=" * 65)

print(f"\n{'Modelo':<12} {'n':>4}  {'Recall médio':>13}  {'Std':>7}")
print("-" * 42)
for model in ['Gemini', 'ChatGPT', 'Claude']:
    sub = data[data['Model'] == model]['Recall']
    print(f"{model:<12} {len(sub):>4}  {sub.mean():>13.4f}  {sub.std():>7.4f}")

difficulty_order = ['Easy', 'Medium', 'Hard']
print(f"\n{'Dificuldade':<12} {'n':>4}  {'Recall médio':>13}  {'Std':>7}")
print("-" * 42)
for diff in difficulty_order:
    sub = data[data['Difficulty'] == diff]['Recall']
    print(f"{diff:<12} {len(sub):>4}  {sub.mean():>13.4f}  {sub.std():>7.4f}")

# ─────────────────────────────────────────────
# PASSO 1 — TWO-WAY ANOVA MANUAL
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("PASSO 1 — TWO-WAY ANOVA (modelo × dificuldade + interação)")
print("=" * 65)

models       = ['Gemini', 'ChatGPT', 'Claude']
difficulties = ['Easy', 'Medium', 'Hard']
a = len(models)
b = len(difficulties)

cell_means = {}
cell_n     = {}
cell_vals  = {}
for m in models:
    for d in difficulties:
        vals = data[(data['Model'] == m) & (data['Difficulty'] == d)]['Recall'].values
        cell_vals[(m, d)]  = vals
        cell_means[(m, d)] = vals.mean() if len(vals) > 0 else np.nan
        cell_n[(m, d)]     = len(vals)

mean_model = {m: data[data['Model'] == m]['Recall'].mean() for m in models}
mean_diff  = {d: data[data['Difficulty'] == d]['Recall'].mean() for d in difficulties}
grand_mean = data['Recall'].mean()
N          = len(data)

SS_A = sum(
    sum(cell_n[(m, d)] for d in difficulties) * (mean_model[m] - grand_mean)**2
    for m in models
)
SS_B = sum(
    sum(cell_n[(m, d)] for m in models) * (mean_diff[d] - grand_mean)**2
    for d in difficulties
)
SS_AxB = sum(
    sum(cell_n[(m, d)] * (cell_means[(m, d)] - mean_model[m] - mean_diff[d] + grand_mean)**2
        for d in difficulties)
    for m in models
)
SS_W = sum(
    sum((v - cell_means[(m, d)])**2 for v in cell_vals[(m, d)])
    for m in models for d in difficulties
)
SS_total = SS_A + SS_B + SS_AxB + SS_W

df_A    = a - 1
df_B    = b - 1
df_AxB  = (a - 1) * (b - 1)
df_W    = N - a - b
df_total = N - 1

MS_A   = SS_A   / df_A
MS_B   = SS_B   / df_B
MS_AxB = SS_AxB / df_AxB
MS_W   = SS_W   / df_W

F_A   = MS_A   / MS_W
F_B   = MS_B   / MS_W
F_AxB = MS_AxB / MS_W

p_A   = 1 - stats.f.cdf(F_A,   df_A,   df_W)
p_B   = 1 - stats.f.cdf(F_B,   df_B,   df_W)
p_AxB = 1 - stats.f.cdf(F_AxB, df_AxB, df_W)

print(f"\n{'Fonte':<18} {'SS':>9}  {'df':>4}  {'MS':>9}  {'F':>8}  {'p-value':>9}")
print("-" * 72)
print(f"{'Factor A (Modelo)':<18} {SS_A:>9.4f}  {df_A:>4}  {MS_A:>9.4f}  {F_A:>8.4f}  {p_A:>9.4f}")
print(f"{'Factor B (Dific.)':<18} {SS_B:>9.4f}  {df_B:>4}  {MS_B:>9.4f}  {F_B:>8.4f}  {p_B:>9.4f}")
print(f"{'Interação A×B':<18} {SS_AxB:>9.4f}  {df_AxB:>4}  {MS_AxB:>9.4f}  {F_AxB:>8.4f}  {p_AxB:>9.4f}")
print(f"{'Within (erro)':<18} {SS_W:>9.4f}  {df_W:>4}  {MS_W:>9.4f}")
print(f"{'Total':<18} {SS_total:>9.4f}  {df_total:>4}")

print(f"\n  Factor A (Modelo)     → F({df_A},{df_W})={F_A:.4f},  p={p_A:.4f}")
if p_A < ALPHA:
    print("  → SIGNIFICATIVO: existe diferença entre os modelos.")
else:
    print("  → NÃO significativo: não há evidência de diferença entre os modelos.")

print(f"\n  Factor B (Dificuldade) → F({df_B},{df_W})={F_B:.4f},  p={p_B:.4f}")
if p_B < ALPHA:
    print("  → SIGNIFICATIVO: a dificuldade influencia o recall.")
else:
    print("  → NÃO significativo: a dificuldade não influencia significativamente o recall.")

print(f"\n  Interação A×B         → F({df_AxB},{df_W})={F_AxB:.4f},  p={p_AxB:.4f}")
if p_AxB < ALPHA:
    print("  → SIGNIFICATIVA: o efeito da dificuldade depende do modelo (e vice-versa).")
else:
    print("  → NÃO significativa: os efeitos de modelo e dificuldade são aditivos/independentes.")

# ─────────────────────────────────────────────
# PASSO 2 — z one-sided: cada modelo > P0?
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"PASSO 2 — H₀: p ≤ {P0:.0%}  vs  H₁: p > {P0:.0%}  (one-sided, α={ALPHA})")
print("Fórmula: z = (p̂ − p₀) / √[p₀(1−p₀)/n]")
print("=" * 65)

z_crit = stats.norm.ppf(1 - ALPHA)
print(f"\n  z crítico (one-sided, α={ALPHA}): {z_crit:.4f}")
print(f"\n  {'Modelo':<10} {'n':>4}  {'p̂':>7}  {'z':>8}  {'p-value':>9}  {'Decisão':>20}")
print("  " + "-" * 62)

rejected_models = []
for model in models:
    vals  = data[data['Model'] == model]['Recall'].values
    n     = len(vals)
    p_hat = vals.mean()
    se    = np.sqrt(P0 * (1 - P0) / n)
    z     = (p_hat - P0) / se
    pval  = 1 - stats.norm.cdf(z)
    decision = "Rejeita H₀" if pval < ALPHA else "Não rejeita H₀"
    if pval < ALPHA:
        rejected_models.append(model)
    print(f"  {model:<10} {n:>4}  {p_hat:>7.4f}  {z:>8.4f}  {pval:>9.4f}  {decision:>20}")

# ─────────────────────────────────────────────
# PASSO 3 — Two-proportion z-test entre modelos que passaram no Passo 2
#           + análise do impacto da dificuldade no melhor modelo
# ─────────────────────────────────────────────
print("\n" + "=" * 65)
print("PASSO 3 — Qual é o melhor modelo?")
print("Fórmula: z = (p1 − p2) / √[p̂pool(1−p̂pool)(1/n₁+1/n₂)]")
print(f"H₀: p2 ≥ p1  vs  H₁: p1 > p2  (one-sided, α={ALPHA})")
print("=" * 65)

if len(rejected_models) < 2:
    print("\n  Menos de 2 modelos rejeitaram H₀ no Passo 2 — Passo 3 não aplicável.")
else:
    # Ordenar por recall médio (melhor primeiro)
    rejected_models_sorted = sorted(
        rejected_models,
        key=lambda m: data[data['Model'] == m]['Recall'].mean(),
        reverse=True
    )
    best   = rejected_models_sorted[0]
    others = rejected_models_sorted[1:]
    pairs  = list(combinations(rejected_models_sorted, 2))
    z_crit = stats.norm.ppf(1 - ALPHA)

    others_str = " / ".join(others)
    print(f"\n  Modelos considerados (ordenados por recall): {rejected_models_sorted}")
    print(f"  H₀: p_{others_str} ≥ p_{best} |  H₁: p_{best} > p_{others_str}")
    print(f"  z crítico: +{z_crit:.4f}  (one-sided, α={ALPHA})")

    for m1, m2 in pairs:
        v1 = data[data['Model'] == m1]['Recall'].values
        v2 = data[data['Model'] == m2]['Recall'].values
        n1, n2 = len(v1), len(v2)
        p1, p2 = v1.mean(), v2.mean()
        p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
        se     = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        z      = (p1 - p2) / se
        pval   = 1 - stats.norm.cdf(z)  # one-sided
        dec    = f"Rejeita H₀ — {m1} é melhor" if pval < ALPHA else "Não rejeita H₀"

        col1 = f"p̂_{m1}"
        col2 = f"p̂_{m2}"
        header = f"\n  {'Par':<22} {col1:>12}  {col2:>12}  {'p̂pool':>7}  {'z':>8}  {'p-value':>9}  {'Decisão':>28}"
        print(header)
        print("  " + "-" * 104)
        print(f"  {m1+' vs '+m2:<22} {p1:>12.4f}  {p2:>12.4f}  {p_pool:>7.4f}  {z:>8.4f}  {pval:>9.4f}  {dec:>28}")

    print("\n  Ranking final (modelos do Passo 3):")
    for i, m in enumerate(rejected_models_sorted, 1):
        mean_r = data[data['Model'] == m]['Recall'].mean()
        print(f"    {i}. {m:<10}  recall médio = {mean_r:.4f}")