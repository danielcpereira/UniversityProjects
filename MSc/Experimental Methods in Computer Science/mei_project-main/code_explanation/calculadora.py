import math

# ── Dados ─────────────────────────────────────────────────────────────────────
grupos = {
    "ChatGPT": {"media": 17.79, "std": 0.378, "n": 10},
    "Claude":  {"media": 17.38, "std": 0.983, "n": 10},
    "Gemini":  {"media": 16.34, "std": 0.629, "n": 10},
}

alpha = 0.01  # 99% confiança

# ── Funções auxiliares ─────────────────────────────────────────────────────────

def lgamma(x):
    c = [76.18009172947146, -86.50532032941677, 24.01409824083091,
         -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5]
    y, tmp = x, x + 5.5
    tmp -= (x + 0.5) * math.log(tmp)
    ser = 1.000000000190015
    for j in range(6):
        y += 1
        ser += c[j] / y
    return -tmp + math.log(2.5066282746310005 * ser / x)

def beta_cf(a, b, x):
    max_it, eps, FPMIN = 200, 3e-7, 1e-30
    qab, qap, qam = a + b, a + 1, a - 1
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < FPMIN: d = FPMIN
    d = 1.0 / d
    h = d
    for m in range(1, max_it + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < FPMIN: d = FPMIN
        c = 1.0 + aa / c
        if abs(c) < FPMIN: c = FPMIN
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h

def incomplete_beta(a, b, x):
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    lbeta = lgamma(a) + lgamma(b) - lgamma(a + b)
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    return front * beta_cf(a, b, x)

def f_pvalue(F, df1, df2):
    x = df2 / (df2 + df1 * F)
    return incomplete_beta(df2 / 2, df1 / 2, x)

def t_pvalue_two_tailed(t, df):
    x = df / (df + t * t)
    return incomplete_beta(df / 2, 0.5, x)

def student_t_test(g1, g2):
    m1, s1, n1 = g1["media"], g1["std"], g1["n"]
    m2, s2, n2 = g2["media"], g2["std"], g2["n"]
    
    se = math.sqrt(s1**2 / n1 + s2**2 / n2)
    t = (m1 - m2) / se
    df = min(n1 - 1, n2 - 1)  # ← regra dos slides: menor dos dois
    
    p = t_pvalue_two_tailed(abs(t), df) / 2  
    return t, df, p

# ── ANOVA ─────────────────────────────────────────────────────────────────────

nomes = list(grupos.keys())
N = sum(g["n"] for g in grupos.values())
k = len(grupos)

GM = sum(g["n"] * g["media"] for g in grupos.values()) / N

SS_B = sum(g["n"] * (g["media"] - GM)**2 for g in grupos.values())
SS_W = sum((g["n"] - 1) * g["std"]**2 for g in grupos.values())
SS_T = SS_B + SS_W

df_B = k - 1
df_W = N - k
df_T = N - 1

MS_B = SS_B / df_B
MS_W = SS_W / df_W
F    = MS_B / MS_W
p_F  = f_pvalue(F, df_B, df_W)

# ── Output ─────────────────────────────────────────────────────────────────────

print("=" * 60)
print("  ANOVA — Comparação de Modelos de IA")
print("=" * 60)

print("\n── Dados de entrada ──")
for nome, g in grupos.items():
    print(f"  {nome:10s}  x̄ = {g['media']:.2f}  σ = {g['std']:.3f}  n = {g['n']}")

print(f"\n  N total = {N}   k = {k}   α = {alpha} (99% confiança)")

print(f"\n── Hipóteses ANOVA ──")
print(f"  H₀: μ₁ = μ₂ = μ₃")
print(f"  H₁: μ₁ ≠ μ₂ ≠ μ₃")

print(f"\n── Média Geral (GM) ──")
print(f"  GM = {GM:.4f}")

print(f"\n── Somas de Quadrados ──")
print(f"  SS Between = {SS_B:.4f}")
print(f"  SS Within  = {SS_W:.4f}")
print(f"  SS Total   = {SS_T:.4f}")

print(f"\n── Tabela ANOVA ──")
print(f"  {'Fonte':<12} {'SS':>10} {'df':>5} {'MS':>10} {'F':>10} {'p':>12}")
print(f"  {'-'*61}")
print(f"  {'Between':<12} {SS_B:>10.4f} {df_B:>5} {MS_B:>10.4f} {F:>10.4f} {p_F:>12.6f}")
print(f"  {'Within':<12} {SS_W:>10.4f} {df_W:>5} {MS_W:>10.4f} {'—':>10} {'—':>12}")
print(f"  {'Total':<12} {SS_T:>10.4f} {df_T:>5} {'—':>10} {'—':>10} {'—':>12}")

print(f"\n  F = {F:.4f}   p = {p_F:.6f}")
if p_F < alpha:
    print(f"  → p < α ({alpha}) — Rejeitar H₀: há diferença significativa entre grupos")
else:
    print(f"  → p > α ({alpha}) — Não rejeitar H₀")

print("\n" + "=" * 60)
print(" Testes t de Student")
print("=" * 60)

nomes_sorted = sorted(grupos.keys(), key=lambda x: grupos[x]["media"], reverse=True)
melhor, meio, pior = nomes_sorted[0], nomes_sorted[1], nomes_sorted[2]

pares = [
    (melhor, pior,  f"H₀: μ_{pior} ≥ μ_{melhor}  |  H₁: μ_{melhor} > μ_{pior}"),
    (melhor, meio,  f"H₀: μ_{meio} ≥ μ_{melhor}  |  H₁: μ_{melhor} > μ_{meio}"),
]

for nome1, nome2, hipoteses in pares:
    t, df, p = student_t_test(grupos[nome1], grupos[nome2])
    print(f"\n  {nome1} vs {nome2}")
    print(f"  {hipoteses}")
    print(f"  tₒ = {t:.4f}   df = {df}   p = {p:.6f}")
    if p < alpha:
        print(f"  → p < α ({alpha}) — Rejeitar H₀ com 99% de confiança ✓")
    else:
        print(f"  → p > α ({alpha}) — Não rejeitar H₀ ✗")

print("\n" + "=" * 60)