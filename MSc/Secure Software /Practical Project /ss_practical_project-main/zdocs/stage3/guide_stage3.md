# Stage 3 - Vulnerabilidades do Baseline — Resumo

## Críticas 

| ID | Vulnerabilidade | Ficheiro | SR | Threat | Estado |
|----|----------------|----------|----|--------|--------|
| V-01 | **SQL Injection** — `prepare_query` faz formatação de string em vez de usar parâmetros reais do psycopg2. Dois pontos: login e listagem de documentos. | `db.py`, `app.py` | SR-20 | T-05 | ✅ Feito |
| V-02 | **OS Command Injection** — nome do ficheiro passado diretamente ao `os.popen()` via `extract_metadata`. | `app.py` | SR-20 | T-07 | ✅ Feito |
| V-03 | **Upload sem validação** — `sanitize_filename` é ineficaz e o seu resultado é ignorado. Sem allowlist de extensões, sem magic bytes, ficheiro guardado com nome original do utilizador. | `utils.py`, `app.py` | SR-07, SR-18, SR-24 | T-04, T-07 | ✅ Feito |

## Altas 

| ID | Vulnerabilidade | Ficheiro | SR | Threat | Estado |
|----|----------------|----------|----|--------|--------|
| V-04 | **IDOR `/documents/<id>`** — rota sem `@login_required` e sem verificação de ownership. Qualquer pessoa acede a qualquer documento. | `app.py` | SR-03, SR-04, SR-06, SR-21 | T-03, T-12 | ✅ Feito |
| V-05 | **Autenticação insegura** — bypass total para admin por precedência de operadores (`or is_admin`). Passwords em plaintext. | `app.py` | SR-01, SR-16 | T-01, T-02 | ✅ Feito |
| V-06 | **IDOR `/documents?user_id=X`** — parâmetro `user_id` aceite sem validação, permite ver documentos de qualquer utilizador. | `app.py` | SR-03, SR-04 | T-12 | ✅ Feito |
| V-07 | **Sem RBAC** — sessão sem campo `role`. Sem decorator `admin_required`. Sem infraestrutura de autorização por papel. | `app.py` | SR-03, SR-11, SR-15, SR-16, SR-28 | T-16 | ✅ Feito |
| V-08 | **XSS refletido via `?uploaded=`** — parâmetro da URL inserido no DOM com `innerHTML` sem sanitização no `script.js`. | `script.js` | SR-20 | T-06 | ✅ Feito |
| V-09 | **XSS armazenado via `data-title`** — Jinja2 escapa corretamente mas o JS volta a inserir o valor com `innerHTML`, anulando a proteção. | `script.js`, `documents.html` | SR-20 | T-06 | ✅ Feito |
| V-10 | **Sem CSRF** — nenhum formulário tem token CSRF. Cookies sem `SameSite`. | todos os templates | SR-35 | T-08 | ✅ Feito |

## Médias 

| ID | Vulnerabilidade | Ficheiro | SR | Threat | Estado |
|----|----------------|----------|----|--------|--------|
| V-11 | **`.env` não está no `.gitignore`** — credenciais e `SECRET_KEY` expostos no repositório. | `.gitignore`, `.env` | SR-39 | T-14 | ✅ Feito |
| V-12 | **`debug=True` em produção** — ativa consola interativa do Werkzeug, permite RCE em caso de erro. | `run.py` | SR-31 | T-13 | ✅ Feito |
| V-13 | **Credenciais da BD hardcoded no Dockerfile** — `ENV POSTGRES_PASSWORD=postgres` na imagem. | `db/Dockerfile` | SR-39 | T-14 | ✅ Feito |
| V-14 | **`SECRET_KEY` com fallback fraco** — se env var não estiver definida, usa `"dev-secret"`. Permite forjar sessões. | `app.py` | SR-14, SR-39 | T-01, T-14 | ✅ Feito |
| V-15 | **Sem rate limiting no login** — brute force e credential stuffing completamente livres. | `app.py` | SR-13, SR-22 | T-02 | ✅ Feito |
| V-16 | **Sem audit logging** — nenhum evento de segurança é registado (logins, acessos, uploads, ações admin). | todos | SR-08, SR-09, SR-26 | T-11 | ✅ Feito |
| V-17 | **Cookies sem flags de segurança** — sem `Secure`, `HttpOnly`, `SameSite` configurados. | `app.py` | SR-14 | T-01 | ✅ Feito |
| V-18 | **Sem security headers HTTP** — sem `CSP`, `X-Frame-Options`, `X-Content-Type-Options`, etc. | `app.py` | SR-20, SR-31 | T-06 | ✅ Feito |
| V-19 | **PyYAML 5.1 vulnerável** — CVEs conhecidos de RCE. Versão atual segura é 6.x. | `requirements.txt` | SR-32 | T-10 | ✅ Feito |
| V-20 | **Volume mount expõe código fonte** — `docker-compose.yml` de dev monta `./web:/app` incluindo `.env`. | `docker-compose.yml` | SR-39 | T-14 | ✅ Feito |
| V-21 | **Sem session timeout** — sessões não expiram por inatividade nem têm duração máxima absoluta (`PERMANENT_SESSION_LIFETIME`). Um token de sessão roubado mantém-se válido indefinidamente. | `app.py` | SR-01, SR-02 | T-01 | ✅ Feito |
| V-22 | **Sem validação de complexidade de password** — ao criar utilizadores novos não há requisitos de comprimento, caracteres especiais, etc. Passwords triviais são aceites sem restrição. | `app.py`, `db.py` | SR-12 | T-02 | ✅ Feito |
| V-23 | **Sem `MAX_CONTENT_LENGTH`** — a aplicação aceita uploads de qualquer tamanho, tornando-a vulnerável a ataques de exaustão de disco e memória (DoS). | `app.py` | SR-23 | T-15 | ✅ Feito |
| V-24 | **Rate limiting ausente no upload** — só o login tem limite de pedidos; o endpoint `/documents/upload` não tem, permitindo flood de uploads e esgotamento de storage. | `app.py` | SR-10 | T-15 | ✅ Feito |
| V-25 | **Sem re-autenticação em ações admin** — ações destrutivas de administração (enable/disable de utilizadores) não pedem confirmação de password, tornando-as exploráveis via CSRF residual ou sessão sequestrada. | `app.py` | SR-27 | T-08, T-16 | ✅ Feito |
| V-26 | **Sem global error handler** — exceções não tratadas expõem stack traces e detalhes internos (nomes de ficheiros, queries SQL, versões de dependências) ao cliente. | `app.py` | SR-30 | T-13 | ✅ Feito |
| V-27 | **Dono não consegue ver quem tem acesso ao seu documento** — não existe endpoint nem UI que liste os utilizadores com quem um documento foi partilhado. | `app.py`, `document_details.html` | SR-34 | T-12 | ✅ Feito |
| V-28 | **Sem proteção/retenção de logs** — os `audit_logs` na BD não têm política de retenção definida nem proteção contra alteração/eliminação por utilizadores com acesso à BD. | `db/init.sql` | SR-09, SR-26 | T-11 | ✅ Feito |
| V-29 | **Sem HTTPS / TLS** — a aplicação serve tráfego em HTTP puro; credenciais e cookies de sessão viajam em claro na rede. Requer configuração de TLS via reverse proxy (ex: nginx + Certbot). | `docker-compose.yml` | SR-05 | T-13 | ✅ Feito |
| V-30 | **Sem backups automatizados** — não existe qualquer mecanismo de backup do volume PostgreSQL. Uma falha de disco ou `docker compose down -v` acidental destrói todos os dados permanentemente. | `docker-compose.yml` | SR-29 | T-15 | ✅ Feito |
| V-31 | **Sem cifra ao nível do volume** — o volume `pgdata` e a pasta `uploads` são armazenados em disco sem cifra. Acesso físico ou root ao host expõe documentos e dados de utilizadores em claro. | `docker-compose.yml` | SR-17 | T-13 | ✅ Feito |
| V-32 | **Sem proteção de metadados de documentos** — os endpoints de listagem e detalhe de documentos expõem metadados (owner, shared_with, path interno) sem validação de ownership server-side; um utilizador autenticado pode obter metadados de documentos que não lhe pertencem nem foram partilhados com ele. | `app.py` | SR-19 | T-12 | ✅ Feito |
| V-33 | **Sem deteção de atividade suspeita** — não existe qualquer mecanismo de alerta ou análise automática sobre os audit logs: logins falhados repetidos, acessos negados em série e padrões anómalos de download não geram qualquer flag, alerta ou resposta automática. | `app.py` | SR-25 | T-02, T-12 | ✅ Feito |
| V-34 | **Sem data minimization** — o registo de utilizadores e os audit logs persistem campos não estritamente necessários (ex: body completo de pedidos, dados de perfil opcionais). Não existe qualquer política definida sobre os campos mínimos a armazenar nos modelos de dados. | `db/init.sql`, `app.py` | SR-33 | — | ✅ Feito |

---

## Ordem de Implementação

| Prioridade | IDs | Foco | Estado |
|------------|-----|------|--------|
| **1ª** | V-05, V-07, V-17, V-14 | Infraestrutura de segurança (auth, roles, cookies) | ✅ Feito |
| **2ª** | V-01, V-02, V-03 | Injeções críticas | ✅ Feito |
| **3ª** | V-04, V-06, V-10 | Controlo de acesso e CSRF | ✅ Feito |
| **4ª** | Endpoints em falta | Download, share, shared, admin | ✅ Feito |
| **5ª** | V-08, V-09, V-18 | XSS e security headers | ✅ Feito |
| **6ª** | V-11, V-12, V-13, V-15, V-16, V-19, V-20 | Hardening e configuração | ✅ Feito |
| **7ª** | V-21, V-22, V-23, V-24 | Session timeout, password policy, upload limits | ✅ Feito |
| **8ª** | V-25, V-26, V-27, V-28 | Admin hardening, error handling, visibilidade de partilhas, log integrity | ✅ Feito |
| **9ª** | V-29, V-30, V-31, V-32, V-33, V-34 | Infraestrutura (HTTPS, backups, cifra de volume), metadados, deteção de anomalias, data minimization | ✅ Feito |