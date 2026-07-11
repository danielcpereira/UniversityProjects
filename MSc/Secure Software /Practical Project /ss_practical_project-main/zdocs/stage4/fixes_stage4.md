# Stage 4 - DevSecOps Pipeline

---

## CI-01 — Secret scanning com Gitleaks: clone incompleto bloqueava análise ✅

**Problema:**
O job `secrets` fazia um checkout com a profundidade padrão do GitHub Actions (`fetch-depth: 1`), que produz um shallow clone com apenas o commit mais recente. O Gitleaks opera sobre o histórico git (`git log -p`) para comparar commits — com um shallow clone, o commit anterior não existe na árvore local e o comando falha com:

```
fatal: ambiguous argument '...<sha>': unknown revision or path not in the working tree.
```

O scan terminava com erro sem ter inspecionado qualquer código, criando uma falsa sensação de segurança.

**Fix:**
Adicionado `fetch-depth: 0` no step de checkout do job `secrets`, forçando um clone completo do histórico:

```yaml
# Antes
- name: Checkout repository
  uses: actions/checkout@v6

# Depois
- name: Checkout repository
  uses: actions/checkout@v6
  with:
    fetch-depth: 0
```

Com o histórico completo, o Gitleaks consegue percorrer todos os commits e detetar segredos introduzidos em qualquer ponto do histórico — não apenas no commit mais recente.

**Ficheiros:** `.github/workflows/1-integration.yml`

---

## CI-02 — SAST com Bandit: configuração via ficheiro e pipeline bloqueante ✅

**Problema:**
O job `sast-bandit` corria com `bandit -r . -x tests || true`, o que significa que mesmo que o Bandit encontrasse vulnerabilidades críticas, o pipeline continuava sem falhar. O scan existia apenas para fins informativos, sem qualquer capacidade de gate de segurança. Adicionalmente, sem ficheiro de configuração, o Bandit analisava diretorias irrelevantes (`.git/`, dependências instaladas, etc.) e não havia forma de gerir falsos positivos ou ajustar a severidade mínima de forma controlada e rastreável.

```yaml
# Antes
- name: Run Bandit
  run: |
    bandit -r . -x tests || true
```

**Fix:**
Removido o `|| true` — o job passa a bloquear o pipeline quando o Bandit reporta findings. A invocação passou a usar `-c .bandit`, que carrega um ficheiro de configuração versionado no repositório onde se define o scope da análise, a severidade mínima e eventuais exclusões justificadas:

```yaml
# Depois
- name: Run Bandit
  run: |
    bandit -r . -c .bandit
```

O ficheiro `.bandit` permite gerir falsos positivos de forma explícita e auditável — em vez de silenciar o pipeline inteiro com `|| true`, cada exclusão é documentada no ficheiro de configuração.

**Ficheiros:** `.github/workflows/1-integration.yml`, `.bandit`

---

## CI-03 — SCA com pip-audit: path incorreto e pipeline não bloqueante ✅

**Problema:**
Dois erros em simultâneo. Primeiro, o step de instalação de dependências usava `pip install -r requirements.txt`, mas o `requirements.txt` está em `web/requirements.txt` — o step falhava imediatamente com:

```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

Segundo, tal como o Bandit, o `pip-audit` corria com `|| true`, tornando-o incapaz de bloquear o pipeline mesmo que encontrasse dependências com CVEs críticos.

```yaml
# Antes
- name: Install dependencies and pip-audit
  run: |
    pip install -r requirements.txt
    pip install pip-audit

- name: Run pip-audit
  run: |
    pip-audit || true
```

**Fix:**
Corrigido o path para `web/requirements.txt`. Adicionado um step separado de upgrade do pip antes da instalação (boa prática para garantir resolução de dependências consistente). Removido o `|| true` — o job passa a bloquear o pipeline se forem encontradas dependências com vulnerabilidades conhecidas:

```yaml
# Depois
- name: Upgrade pip
  run: |
    python -m pip install --upgrade pip

- name: Install dependencies and pip-audit
  run: |
    pip install -r web/requirements.txt
    pip install pip-audit

- name: Run pip-audit
  run: |
    pip-audit
```

Com estas alterações, o SCA passa a ser um verdadeiro security gate: dependências com CVEs conhecidos bloqueam o build antes de qualquer imagem ser publicada.

**Ficheiros:** `.github/workflows/1-integration.yml`

---

## CI-04 — Container scanning, SBOM e publicação ordenada ✅

**Problema:**
O job `build-and-push` original construía e publicava a imagem num único step (`push: true`), sem qualquer análise de segurança intermédia. Isto significa que a imagem era publicada no GHCR antes de ser inspecionada — um atacante que observasse o registry poderia usar uma imagem não verificada, e uma imagem com vulnerabilidades críticas chegaria ao registry mesmo que fosse depois detetada.

```yaml
# Antes — build e push num único step, sem scan nem SBOM
- name: Build and push web image
  uses: docker/build-push-action@v7
  with:
    context: ./web
    push: true
    tags: ${{ env.WEB_SHA_TAG }}
    provenance: false
```

**Fix:**
O job foi reestruturado em quatro fases ordenadas: build local → scan → SBOM → push. A imagem só é publicada depois de ter passado pelo Trivy e de ter um SBOM gerado.

```yaml
# 1. Build local (sem push)
- name: Build web image locally
  uses: docker/build-push-action@v7
  with:
    context: ./web
    push: false
    load: true
    tags: ${{ env.WEB_SHA_TAG }}
    provenance: false

# 2. Scan da imagem com Trivy (exit-code: "0" — reporta sem bloquear)
- name: Scan Docker image with Trivy
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ env.WEB_SHA_TAG }}
    format: table
    exit-code: "0"
    severity: HIGH,CRITICAL

# 3. Geração do SBOM em CycloneDX
- name: Generate SBOM
  uses: anchore/sbom-action@v0
  with:
    image: ${{ env.WEB_SHA_TAG }}
    format: cyclonedx-json
    output-file: sbom.cdx.json

# 4. Upload do SBOM como artefacto do workflow
- name: Upload SBOM
  uses: actions/upload-artifact@v7
  with:
    name: sbom-${{ github.sha }}
    path: sbom.cdx.json

# 5. Push apenas após scan e SBOM
- name: Push web image
  uses: docker/build-push-action@v7
  with:
    context: ./web
    push: true
    tags: ${{ env.WEB_SHA_TAG }}
    provenance: false
```

O `exit-code: "0"` no Trivy significa que o scan reporta findings mas não bloqueia — útil para ter visibilidade inicial sem parar o pipeline por vulnerabilidades nos pacotes base da imagem que ainda não têm fix disponível. Para tornar o Trivy bloqueante em HIGH/CRITICAL basta mudar para `exit-code: "1"`.

O SBOM é gerado a partir da imagem construída (não do código fonte), garantindo que o inventário reflete exatamente o que foi empacotado — incluindo pacotes do sistema operativo e dependências transitivas que não aparecem no `requirements.txt`.

**Ficheiros:** `.github/workflows/1-integration.yml`

---

## CI-05 — Pipeline com security gates em cascata ✅

**Problema:**
No CI original, o job `build-and-push` dependia apenas do job `test`. Os jobs de segurança (`secrets`, `sast-bandit`, `sca`) corriam em paralelo mas o build não esperava por eles — uma imagem podia ser publicada mesmo que o secret scanning ou o SAST tivessem falhado.

**Fix:**
O job `build-and-push` passou a declarar dependência explícita de todos os jobs de segurança:

```yaml
# Antes
build-and-push:
  needs: [test]

# Depois
build-and-push:
  needs: [test, secrets, sast-bandit, sca]
```

O pipeline tem agora a seguinte estrutura em cascata — a imagem só é construída e publicada se todos os gates anteriores passarem:

```
test ──────────┐
secrets ───────┤
sast-bandit ───┼──► build-and-push
sca ───────────┘
```

**Ficheiros:** `.github/workflows/1-integration.yml`

---

## CD-01 — Testes dinâmicos de segurança no pipeline de CD ✅

**Problema:**
O `2-delivery.yml` original apenas executava um smoke test de autenticação (`test_delivery_auth_flow.py`). Não existia qualquer validação de segurança em runtime — controlos críticos como IDOR entre utilizadores, autorização por role, invalidação de sessão após logout, proteção CSRF e validação de input nunca eram testados contra a aplicação em execução. Era possível promover uma imagem com vulnerabilidades de controlo de acesso ativas.

**Fix:**
Criado `tests/test_deployed_api.py` com testes dinâmicos black-box que enviam pedidos HTTP reais à aplicação em execução. Os testes são organizados pelos dois controlos OWASP verificados:

**Access Control:**
- Todos os endpoints protegidos rejeitam acesso não autenticado (`/documents`, `/shared`, `/admin/users`)
- Login cria sessão autenticada; logout invalida a sessão
- Credenciais inválidas são rejeitadas
- IDOR: Alice não consegue aceder a documentos do Bob (`/documents/<id>`, `/documents/<id>/download`)
- RBAC: utilizador regular não acede a `/admin/users` nem executa ações de admin
- Acesso a documentos partilhados requer autenticação
- CSRF: uploads e login sem token são rejeitados (400/403)

**Input Validation:**
- IDs de documentos malformados (`abc`, `../etc`, `-1`, `0`) retornam 400/403/404, nunca 500
- Ficheiros com extensão não permitida (`.sh`) são rejeitados antes da encriptação
- Ficheiros com magic bytes incorretos (`.pdf` sem cabeçalho PDF) são rejeitados
- Uploads superiores a 10 MB são rejeitados
- Headers de segurança presentes em todas as respostas (`X-Frame-Options`, `X-Content-Type-Options`, `Content-Security-Policy`)

Para evitar disparar o rate limiter da app (`5 POST /login por minuto por username`), os testes partilham sessões via `_get_session()` — cada utilizador faz login uma única vez por run. Os testes que precisam de logout usam `_fresh_session()` com `sleep(1)` para espaçar os pedidos.

Adicionado ao `2-delivery.yml` como gate bloqueante após o smoke test:

```yaml
- name: Run dynamic API security tests
  env:
    APP_BASE_URL: http://localhost
  run: |
    pytest -v tests/test_deployed_api.py
```

Sem `continue-on-error` — uma falha de segurança bloqueia a promoção da imagem.

**Ficheiros:** `tests/test_deployed_api.py`, `.github/workflows/2-delivery.yml`

---

## CD-02 — OWASP ZAP baseline scan no pipeline de CD ✅

**Problema:**
Nenhum scan automatizado de segurança era executado contra a aplicação em execução no ambiente de staging. Vulnerabilidades genéricas de runtime — headers em falta, configuração insegura, padrões de injeção comuns, problemas de autenticação/sessão — não eram detetadas antes da promoção da imagem.

**Fix:**
Adicionado o OWASP ZAP baseline scan ao `2-delivery.yml` após os testes dinâmicos, em modo report-only (`continue-on-error: true`):

```yaml
- name: Run OWASP ZAP baseline scan
  uses: zaproxy/action-baseline@v0.14.0
  continue-on-error: true
  with:
    target: "http://localhost"
    allow_issue_writing: false
```

O ZAP corre em modo report-only porque:
1. Pode produzir falsos positivos que precisam de revisão antes de se tornarem gates bloqueantes
2. A app não expõe OpenAPI spec nem interface crawlável, por isso o ZAP descobre apenas os endpoints que encontra organicamente (`/`, `/robots.txt`, `/sitemap.xml`) — findings genéricos como headers em falta são úteis, mas findings de lógica aplicacional (IDOR, autorização) requerem os testes dinâmicos do CD-01
3. O PDF recomenda explicitamente começar em report-only: *"ZAP should initially run in report-only mode; later, teams may decide whether specific ZAP findings should block deployment"*

Para tornar o ZAP bloqueante em findings high-risk basta mudar para `continue-on-error: false`.

A estrutura final do pipeline de CD é:

```
pull image → staging container → smoke test (blocking)
  → dynamic security tests (blocking)
  → ZAP baseline scan (report-only)
  → promote to :dev
  → cleanup
```

**Ficheiros:** `.github/workflows/2-delivery.yml`

---

## CD-03 — Correção de findings do OWASP ZAP ✅

**Problema:**
Após o primeiro run do ZAP baseline scan, foram reportados 8 warnings. Três correspondiam a problemas reais e corrigíveis nos headers HTTP da aplicação e do servidor nginx.

**Fix 1 — Server version disclosure (`nginx/nginx.conf`)**

O nginx expunha a versão exata no header `Server: nginx/1.29.8` em todas as respostas, facilitando reconnaissance por parte de um atacante.

```nginx
# Antes
server {
    listen 80;
    server_name _;
    ...
}

# Depois
server {
    listen 80;
    server_name _;
    server_tokens off;
    ...
}
```

Resultado: `WARN-NEW: Server Leaks Version Information [10036]` → `PASS: HTTP Server Response Header [10036]`

**Fix 2 — CSP incompleto (`web/app/app.py`)**

O CSP original (`default-src 'self'`) não definia `form-action` nem `frame-ancestors`, deixando essas diretivas sem fallback explícito.

```python
# Antes
response.headers["Content-Security-Policy"] = "default-src 'self'"

# Depois
response.headers["Content-Security-Policy"] = "default-src 'self'; form-action 'self'; frame-ancestors 'none'"
```

`form-action 'self'` impede que formulários submetam dados para origens externas. `frame-ancestors 'none'` complementa o `X-Frame-Options: DENY` já existente com a diretiva CSP equivalente, compatível com browsers modernos.

Resultado: `WARN-NEW: CSP: Failure to Define Directive with No Fallback [10055]` → `PASS: CSP [10055]`

**Fix 3 — Permissions Policy ausente (`web/app/app.py`)**

Nenhum header `Permissions-Policy` era enviado, o que significa que o browser não tinha indicação explícita de que a app não necessita de acesso a geolocalização, microfone ou câmara.

```python
# Adicionado
response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
```

Mesmo que código malicioso fosse injetado na página, o browser recusaria acesso a estes recursos porque o servidor declarou explicitamente que não os necessita.

Resultado: `WARN-NEW: Permissions Policy Header Not Set [10063]` → `PASS: Permissions Policy Header Not Set [10063]`

**Fix 4 — COEP, COOP e CORP ausentes (`web/app/app.py`)**

Nenhum header `Cross-Origin-Embedder-Policy`, `Cross-Origin-Opener-Policy` nem `Cross-Origin-Resource-Policy` era enviado, expondo a app a ataques de cross-origin information leakage e Spectre-style side-channel attacks.

```python
# Adicionado
response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
```

`COEP: require-corp` garante que todos os recursos carregados pela página declaram explicitamente que permitem ser embebidos — impede que recursos cross-origin não cooperantes sejam carregados sem consentimento explícito. `COOP: same-origin` isola o browsing context group da página, impedindo que janelas abertas por ou que abrem a app possam aceder ao seu `window` object — mitiga ataques Spectre que exploram `SharedArrayBuffer` e `performance.now()`. `CORP: same-origin` declara que os recursos servidos por esta app só podem ser carregados por páginas da mesma origem, complementando o COEP e prevenindo ataques de cross-origin read como Spectre e cross-site script inclusion (XSSI).

Resultado: `WARN-NEW: Cross-Origin-Embedder-Policy Header Missing [90004]` → `PASS: Cross-Origin-Embedder-Policy Header Missing [90004]`

**Fix 5 — Cache-Control e Pragma ausentes (`web/app/app.py`)**

Sem headers de cache explícitos, browsers e proxies intermédios podiam armazenar respostas de páginas autenticadas (documentos, sessões, dados de utilizador), expondo informação sensível a outros utilizadores do mesmo dispositivo ou proxy.

```python
# Adicionado
response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
response.headers["Pragma"] = "no-cache"
```

`Cache-Control: no-store` impede qualquer armazenamento da resposta em cache (browser ou proxy). `no-cache` obriga a revalidação com o servidor antes de usar uma entrada em cache. `must-revalidate` garante que entradas expiradas não são servidas offline. `Pragma: no-cache` é o equivalente HTTP/1.0 — incluído para compatibilidade com proxies legados que não interpretam `Cache-Control`.

**Ficheiros:** `web/app/app.py`

---

**Findings não corrigidos e justificação:**

| Warning | Justificação |
|---------|-------------|
| User Controllable HTML Element (XSS) [10031] | Falso positivo — Jinja2 faz auto-escape por omissão; confirmado pela ausência de `\| safe` ou `Markup()` nos templates |
| Non-Storable Content [10049] | Comportamento correto — redirects e páginas autenticadas não devem ser cacheadas |
| Authentication Request Identified [10111] | Puramente informativo |
| Session Management Response Identified [10112] | Puramente informativo |

**Resultado final:** 0 failures, 4 warnings justificados, 63 passes.

**Ficheiros:** `nginx/nginx.conf`, `web/app/app.py`