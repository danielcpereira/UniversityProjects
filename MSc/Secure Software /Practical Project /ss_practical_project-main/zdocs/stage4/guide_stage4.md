# Stage 4 - DevSecOps Pipeline — Resumo

## Problemas no Pipeline Baseline

| ID | Problema | Ficheiro | SR | Threat | Estado |
|----|----------|----------|----|--------|--------|
| CI-01 | **Secret scanning com Gitleaks: clone incompleto bloqueava análise** — checkout com `fetch-depth: 1` (shallow clone) impedia o Gitleaks de percorrer o histórico git; o scan falhava com `fatal: ambiguous argument` sem inspecionar qualquer código, criando falsa sensação de segurança. | `.github/workflows/1-integration.yml` | SR-39 | T-14 | ✅ Feito |
| CI-02 | **SAST com Bandit: pipeline não bloqueante e sem ficheiro de configuração** — `bandit -r . -x tests \|\| true` tornava o SAST puramente informativo; vulnerabilidades críticas não bloqueavam o build. Sem `.bandit`, o Bandit analisava diretorias irrelevantes e não havia forma auditável de gerir falsos positivos. | `.github/workflows/1-integration.yml`, `.bandit` | SR-37 | T-14, T-18 | ✅ Feito |
| CI-03 | **SCA com pip-audit: path incorreto e pipeline não bloqueante** — `pip install -r requirements.txt` falhava imediatamente (`No such file or directory`) pois o ficheiro está em `web/requirements.txt`. Adicionalmente, `pip-audit \|\| true` tornava o scan incapaz de bloquear o pipeline mesmo com CVEs críticos nas dependências. | `.github/workflows/1-integration.yml` | SR-32, SR-37 | T-10 | ✅ Feito |
| CI-04 | **Container scanning, SBOM e publicação ordenada ausentes** — o job `build-and-push` original construía e publicava a imagem num único step (`push: true`) sem qualquer análise de segurança intermédia; a imagem chegava ao registry antes de ser inspecionada, sem inventário de componentes (SBOM). | `.github/workflows/1-integration.yml` | SR-37, SR-38 | T-10, T-14 | ✅ Feito |
| CI-05 | **Sem security gates em cascata** — o job `build-and-push` dependia apenas de `test`; os jobs de segurança (`secrets`, `sast-bandit`, `sca`) corriam em paralelo mas o build não esperava por eles, permitindo publicar uma imagem mesmo que o secret scanning ou o SAST tivessem falhado. | `.github/workflows/1-integration.yml` | SR-36, SR-37 | T-09, T-14, T-18 | ✅ Feito |
| CD-01 | **Ausência de testes dinâmicos de segurança no pipeline de CD** — o `2-delivery.yml` original apenas executava um smoke test de autenticação (`test_delivery_auth_flow.py`), sem qualquer validação de segurança em runtime. Controlos críticos como IDOR, autorização por role, invalidação de sessão, validação de input e proteção CSRF nunca eram testados contra a aplicação em execução, tornando possível promover uma imagem com vulnerabilidades de controlo de acesso. | `.github/workflows/2-delivery.yml`, `tests/test_deployed_api.py` | SR-04, SR-06, SR-10, SR-37 | T-01, T-03, T-09 | ✅ Feito |
| CD-02 | **Ausência de DAST automatizado no pipeline de CD** — nenhum scan automatizado de segurança era executado contra a aplicação em execução no ambiente de staging; vulnerabilidades genéricas de runtime (headers em falta, configuração insegura, padrões de injeção comuns) não eram detetadas antes da promoção da imagem. | `.github/workflows/2-delivery.yml` | SR-37, SR-38 | T-10, T-14 | ✅ Feito |
| CD-03 | **Findings do OWASP ZAP corrigidos** — após o primeiro run do ZAP foram reportados 8 warnings; 3 correspondiam a problemas reais: server version disclosure no nginx, CSP sem `form-action` e `frame-ancestors`, e ausência de `Permissions-Policy`. Os restantes 5 foram analisados e classificados como falsos positivos ou informativos. | `nginx/nginx.conf`, `web/app/app.py` | SR-37 | T-14 | ✅ Feito |

---

## Ordem de Implementação

| Prioridade | IDs | Foco | Estado |
|------------|-----|------|--------|
| **1ª** | CI-05 | Cascade gate: `build-and-push` depende de todos os jobs de segurança | ✅ Feito |
| **2ª** | CI-01 | Secret scanning funcional: `fetch-depth: 0` no Gitleaks | ✅ Feito |
| **3ª** | CI-02 | SAST bloqueante: remover `\|\| true`, adicionar `.bandit` | ✅ Feito |
| **4ª** | CI-03 | SCA bloqueante: corrigir path `web/requirements.txt`, remover `\|\| true` | ✅ Feito |
| **5ª** | CI-04 | Container scan + SBOM + push ordenado | ✅ Feito |
| **6ª** | CD-01 | Testes dinâmicos de segurança bloqueantes no CD: IDOR, autorização, sessão, CSRF, input validation | ✅ Feito |
| **7ª** | CD-02 | OWASP ZAP baseline scan no CD em modo report-only | ✅ Feito |
| **8ª** | CD-03 | Análise e correção de findings do ZAP: server_tokens off, CSP completo, Permissions-Policy | ✅ Feito |

---

## Análise dos Findings do OWASP ZAP

Após correr o ZAP baseline scan no pipeline de CD, os findings foram analisados e tratados iterativamente. Resultado final: **0 failures, 4 warnings justificados, 63 passes**.

### Findings corrigidos

| Warning | Rule ID | Fix | Ficheiro |
|---------|---------|-----|---------|
| Server Leaks Version via "Server" header | 10036 | `server_tokens off;` no nginx | `nginx/nginx.conf` |
| CSP: Failure to Define Directive with No Fallback | 10055 | Adicionado `form-action 'self'` e `frame-ancestors 'none'` ao CSP | `web/app/app.py` |
| Permissions Policy Header Not Set | 10063 | Adicionado header `Permissions-Policy` com `geolocation=(), microphone=(), camera=()` | `web/app/app.py` |
| Cross-Origin-Embedder-Policy Header Missing | 90004 | Adicionados headers `COEP: require-corp`, `COOP: same-origin` e `CORP: same-origin` | `web/app/app.py` |
| Cache-Control ausente | — | Adicionados `Cache-Control: no-store, no-cache, must-revalidate` e `Pragma: no-cache` para prevenir caching de respostas autenticadas | `web/app/app.py` |

### Findings justificados (não corrigidos)

| Warning | Rule ID | Justificação |
|---------|---------|-------------|
| User Controllable HTML Element Attribute (Potential XSS) | 10031 | Falso positivo — os templates `login.html` e `register.html` não contêm `\| safe` nem `Markup()`; o Jinja2 faz auto-escape de todos os valores por omissão |
| Non-Storable Content | 10049 | Comportamento correto por design — redirects e páginas autenticadas não devem ser cacheadas |
| Authentication Request Identified | 10111 | Puramente informativo — o ZAP detetou o formulário de login; não representa uma vulnerabilidade |
| Session Management Response Identified | 10112 | Puramente informativo — o ZAP detetou gestão de sessão; não representa uma vulnerabilidade |