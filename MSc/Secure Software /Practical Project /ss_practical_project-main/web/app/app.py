import datetime
import functools
import logging
import pathlib
import os
import traceback
from urllib import response
import psycopg2
import flask
import dotenv
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from . import audit
from . import db
from . import utils
from werkzeug.utils import secure_filename
import bcrypt

dotenv.load_dotenv()

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "docdb")

UPLOAD_FOLDER = "uploads"
MAX_UPLOAD_MB = 10  # V-23 — tamanho máximo por upload (em MB)

# V-21 — timeout de inatividade (lado servidor)
INACTIVITY_TIMEOUT = datetime.timedelta(minutes=5)

logger = logging.getLogger(__name__)

def get_db():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME,
    )

def create_app():
    app = flask.Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    # V-14 — secret
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY is not defined")
    app.secret_key = secret_key

    # V-10 — CSRF protection
    csrf = CSRFProtect(app)

    # Rate limiting — protecção contra brute force e credential stuffing
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[],
        storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    )
    app.limiter = limiter

    # V-17 — cookies
    app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # V-21 — duração máxima absoluta da sessão (4 horas)
    app.config["PERMANENT_SESSION_LIFETIME"] = datetime.timedelta(hours=4)

    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    # V-23 — limitar tamanho máximo de upload para evitar DoS por exaustão de disco/memória
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

    security_logger = logging.getLogger("security")
    if not security_logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.WARNING)
        security_logger.addHandler(handler)
        security_logger.setLevel(logging.WARNING)

    register_routes(app)

    return app

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

def extract_metadata(filepath):
    try:
        p = pathlib.Path(filepath)
        size = p.stat().st_size
        ext = p.suffix.lower()
        return f"size_bytes={size} extension={ext}"
    except Exception:
        return ""

def login_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in flask.session:
            flask.flash("Please log in first.", "error")
            return flask.redirect(flask.url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

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

def sudo_required(fn):
    SUDO_GRACE_SECONDS = 60

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

        flask.session["sudo_next_endpoint"] = flask.request.endpoint
        flask.session["sudo_next_view_args"] = flask.request.view_args or {}
        return flask.redirect(flask.url_for("admin_confirm_password"))

    return wrapper


def register_routes(app):

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = ("default-src 'self'; ""form-action 'self'; ""frame-ancestors 'none'")
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        return response

    # V-21 — verificar timeout de inatividade em cada request autenticado
    @app.before_request
    def check_session_timeout():
        if "user_id" not in flask.session:
            return

        last = flask.session.get("last_activity")
        if last:
            last_dt = datetime.datetime.fromisoformat(last)
            if datetime.datetime.now(datetime.timezone.utc) - last_dt > INACTIVITY_TIMEOUT:
                flask.session.clear()
                flask.flash("Session expired due to inactivity. Please log in again.", "error")
                return flask.redirect(flask.url_for("login"))

        flask.session["last_activity"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    @app.errorhandler(429)
    def ratelimit_handler(e):
        flask.flash("Too many attempts. Please try again later.", "error")
        retry_after = getattr(e, "retry_after", None)
        if flask.request.endpoint == "upload_document":
            response = flask.make_response(flask.redirect(flask.url_for("documents_page")), 429)
        else:
            response = flask.make_response(flask.render_template("login.html"), 429)
        if retry_after:
            response.headers["Retry-After"] = str(int(retry_after.total_seconds()))
        return response

    @app.errorhandler(413)
    def request_too_large(e):
        flask.flash(f"File too large. Maximum allowed size: {MAX_UPLOAD_MB} MB.", "error")
        return flask.redirect(flask.url_for("documents_page"))

    @app.errorhandler(400)
    def bad_request(e):
        return flask.render_template("error.html", code=400, message="Invalid request."), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return flask.render_template("error.html", code=401, message="Not authenticated."), 401

    @app.errorhandler(403)
    def forbidden(e):
        return flask.render_template("error.html", code=403, message="Access denied."), 403

    @app.errorhandler(404)
    def not_found(e):
        return flask.render_template("error.html", code=404, message="Page not found."), 404

    @app.errorhandler(500)
    def internal_error(e):
        logger.error("500 error: %s", e, exc_info=True)
        return flask.render_template("error.html", code=500, message="Internal server error."), 500

    @app.errorhandler(Exception)
    def unhandled_exception(e):
        logger.error(
            "Unhandled exception on %s %s:\n%s",
            flask.request.method,
            flask.request.path,
            traceback.format_exc(),
        )
        return flask.render_template("error.html", code=500, message="An unexpected error occurred."), 500

    @app.route("/")
    def index():
        if flask.session.get("user_id"):
            return flask.redirect(flask.url_for("documents_page"))
        return flask.redirect(flask.url_for("login"))

    def _login_ip_key():
        return f"ip:{get_remote_address()}"

    def _login_user_key():
        username = flask.request.form.get("username", "").lower().strip()
        return f"user:{username}"

    def _upload_user_key():
        user_id = flask.session.get("user_id", "anonymous")
        return f"upload_user:{user_id}"

    def _upload_ip_key():
        return f"upload_ip:{get_remote_address()}"

    @app.route("/login", methods=["GET", "POST"])
    @app.limiter.limit("10 per minute; 30 per hour", key_func=_login_ip_key, methods=["POST"])
    @app.limiter.limit("5 per minute; 20 per hour", key_func=_login_user_key, methods=["POST"])
    def login():
        if flask.request.method == "POST":
            username = flask.request.form.get("username", "")
            password = flask.request.form.get("password", "")

            conn = get_db()
            cur = conn.cursor()

            user = db.get_user_by_username(cur, username)

            if user and not user[3] and bcrypt.checkpw(password.encode("utf-8"), user[2].encode("utf-8")):
                flask.session.clear()
                flask.session.permanent = True
                flask.session["user_id"] = user[0]
                flask.session["username"] = user[1]
                flask.session["role"] = user[4]
                flask.session["last_activity"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                audit.log_event(cur, audit.LOGIN_SUCCESS, user_id=user[0], username=user[1])
                conn.commit()
                cur.close()
                conn.close()
                return flask.redirect(flask.url_for("documents_page"))

            # Login falhado
            failed_user_id = user[0] if user else None
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

            conn.commit()
            cur.close()
            conn.close()
            flask.flash("Invalid credentials.", "error")

        return flask.render_template("login.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if flask.session.get("user_id"):
            return flask.redirect(flask.url_for("documents_page"))

        if flask.request.method == "POST":
            username = flask.request.form.get("username", "").strip()
            password = flask.request.form.get("password", "")
            confirm  = flask.request.form.get("confirm_password", "")

            if not username or not password:
                flask.flash("Username and password are required.", "error")
                return flask.render_template("register.html")

            if password != confirm:
                flask.flash("Passwords do not match.", "error")
                return flask.render_template("register.html")

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
                flask.flash("Account created successfully. Please log in.", "success")
                return flask.redirect(flask.url_for("login"))
            except psycopg2.errors.UniqueViolation:
                conn.rollback()
                flask.flash("Username already exists.", "error")
            finally:
                cur.close()
                conn.close()

        return flask.render_template("register.html")

    @app.route("/logout")
    def logout():
        user_id = flask.session.get("user_id")
        username = flask.session.get("username")
        conn = get_db()
        cur = conn.cursor()
        audit.log_event(cur, audit.LOGOUT, user_id=user_id, username=username)
        conn.commit()
        cur.close()
        conn.close()
        flask.session.clear()
        return flask.redirect(flask.url_for("login"))

    @app.route("/documents/<int:document_id>")
    @login_required
    def document_details(document_id):
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT id, owner_id, title, filename, metadata
            FROM documents
            WHERE id = %s
            """,
            (document_id,)
        )
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            flask.abort(404)

        current_user_id = flask.session.get("user_id")
        owner_id = row[1]
        is_owner = (current_user_id == owner_id)

        # V-04 — só o dono ou utilizador com partilha explícita pode aceder
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

        audit.log_event(cur, audit.DOCUMENT_VIEW, user_id=current_user_id,
                        username=flask.session.get("username"),
                        details=f"document_id={document_id}")

        # Busca o username do owner
        cur.execute("SELECT username FROM users WHERE id = %s", (owner_id,))
        owner_row = cur.fetchone()
        owner_username = owner_row[0] if owner_row else "Unknown"

        shared_with_rows = db.get_shares_for_document(cur, document_id, owner_id) if is_owner else []

        conn.commit()
        cur.close()
        conn.close()

        document = {
            "id": row[0],
            "owner": owner_username,
            "title": row[2],
            "filename": row[3],
            "is_owner": is_owner,
        }

        shared_with = [
            {"id": r[0], "username": r[1]}
            for r in shared_with_rows
        ]

        return flask.render_template("document_details.html", document=document, shared_with=shared_with)

    @app.route("/documents")
    @login_required
    def documents_page():
        requested_user_id = flask.request.args.get("user_id")
        current_user_id = flask.session.get("user_id")

        if requested_user_id and str(requested_user_id) != str(current_user_id):
            flask.abort(403)

        owner_id = current_user_id

        conn = get_db()
        cur = conn.cursor()

        docs = get_documents_for_user(cur, owner_id)
        shared_docs = db.get_shared_documents_for_user(cur, current_user_id)

        cur.close()
        conn.close()

        documents = [
            {
                "id": d[0],
                "title": d[1],
                "filename": d[2],
                "uploaded_at": d[3],
            }
            for d in docs
        ]

        shared_documents = [
            {
                "id": r[0],
                "title": r[1],
                "uploaded_at": r[3],
                "owner_username": r[4],
            }
            for r in shared_docs
        ]

        return flask.render_template(
            "documents.html",
            documents=documents,
            shared_documents=shared_documents,
            requested_user_id=owner_id,
            current_user_id=current_user_id,
            username=flask.session.get("username"),
        )

    @app.route("/documents/upload", methods=["POST"])
    @login_required
    @app.limiter.limit("10 per minute; 30 per hour", key_func=_upload_user_key)
    @app.limiter.limit("20 per minute; 60 per hour", key_func=_upload_ip_key)
    def upload_document():
        user_id = flask.session.get("user_id")
        title = flask.request.form.get("title", "Untitled")
        uploaded_file = flask.request.files.get("document")

        if not uploaded_file or uploaded_file.filename == "":
            flask.flash("Please choose a file.", "error")
            return flask.redirect(flask.url_for("documents_page"))

        filename = utils.sanitize_filename(uploaded_file.filename)
        if not filename:
            flask.flash("File type not allowed.", "error")
            return flask.redirect(flask.url_for("documents_page"))

        ext = os.path.splitext(filename)[1].lower()
        if not utils.validate_magic_bytes(uploaded_file.stream, ext):
            flask.flash("File content does not match its extension.", "error")
            return flask.redirect(flask.url_for("documents_page"))

        upload_folder = BASE_DIR / app.config["UPLOAD_FOLDER"]
        upload_folder.mkdir(parents=True, exist_ok=True)

        destination = upload_folder / filename

        from app import crypto

        raw_bytes = uploaded_file.read()
        encrypted_bytes = crypto.encrypt_file(raw_bytes)
        with open(destination, "wb") as f:
            f.write(encrypted_bytes)

        metadata = extract_metadata(destination)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO documents (owner_id, title, filename, metadata)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, title, filename, metadata),
        )
        audit.log_event(cur, audit.DOCUMENT_UPLOAD, user_id=user_id,
                        username=flask.session.get("username"),
                        details=f"filename={filename} title={title!r}")
        conn.commit()
        cur.close()
        conn.close()

        flask.flash(f"Document uploaded: {title}", "success")
        return flask.redirect(flask.url_for("documents_page"))

    @app.route("/health")
    def health():
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.close()
            conn.close()
            return {"status": "ok"}, 200
        except Exception:
            return {"status": "error"}, 500

    @app.route("/documents/<int:document_id>/download")
    @login_required
    def download_document(document_id):
        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, owner_id, filename FROM documents WHERE id = %s",
            (document_id,)
        )
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return "Document not found", 404

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

        cur.close()
        conn.close()

        conn2 = get_db()
        cur2 = conn2.cursor()
        audit.log_event(cur2, audit.DOCUMENT_DOWNLOAD, user_id=flask.session.get("user_id"),
                        username=flask.session.get("username"),
                        details=f"document_id={document_id}")
        conn2.commit()
        cur2.close()
        conn2.close()

        upload_folder = BASE_DIR / app.config["UPLOAD_FOLDER"]
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

    @app.route("/documents/<int:document_id>/share", methods=["POST"])
    @login_required
    def share_document(document_id):
        current_user_id = flask.session.get("user_id")
        shared_with_id = flask.request.form.get("shared_with")

        if not shared_with_id:
            flask.flash("User not specified.", "error")
            return flask.redirect(flask.url_for("document_details", document_id=document_id))

        try:
            shared_with_id = int(shared_with_id)
        except ValueError:
            flask.abort(400)

        if shared_with_id == current_user_id:
            flask.flash("You cannot share a document with yourself.", "error")
            return flask.redirect(flask.url_for("document_details", document_id=document_id))

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, owner_id FROM documents WHERE id = %s",
            (document_id,)
        )
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return "Document not found", 404

        if row[1] != current_user_id:
            cur.close()
            conn.close()
            flask.abort(403)

        target = db.get_user_by_id(cur, shared_with_id)
        if not target or target[2]:
            cur.close()
            conn.close()
            flask.flash("User not found.", "error")
            return flask.redirect(flask.url_for("document_details", document_id=document_id))

        db.share_document(cur, document_id, current_user_id, shared_with_id)
        audit.log_event(cur, audit.DOCUMENT_SHARE, user_id=current_user_id,
                        username=flask.session.get("username"),
                        details=f"document_id={document_id} shared_with_id={shared_with_id}")
        conn.commit()
        cur.close()
        conn.close()

        flask.flash("Document shared successfully.", "success")
        return flask.redirect(flask.url_for("document_details", document_id=document_id))

    @app.route("/documents/<int:document_id>/revoke", methods=["POST"])
    @login_required
    def revoke_share(document_id):
        current_user_id = flask.session.get("user_id")
        shared_with_id = flask.request.form.get("shared_with_id")

        if not shared_with_id:
            flask.abort(400)

        try:
            shared_with_id = int(shared_with_id)
        except ValueError:
            flask.abort(400)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, owner_id FROM documents WHERE id = %s",
            (document_id,)
        )
        row = cur.fetchone()

        if not row:
            cur.close()
            conn.close()
            return "Document not found", 404

        if row[1] != current_user_id:
            cur.close()
            conn.close()
            flask.abort(403)

        revoked = db.revoke_share(cur, document_id, current_user_id, shared_with_id)
        if revoked:
            audit.log_event(cur, audit.DOCUMENT_SHARE, user_id=current_user_id,
                            username=flask.session.get("username"),
                            details=f"revoke document_id={document_id} shared_with_id={shared_with_id}")
        conn.commit()
        cur.close()
        conn.close()

        flask.flash("Access revoked successfully." if revoked else "Share not found.",
                    "success" if revoked else "error")
        return flask.redirect(flask.url_for("document_details", document_id=document_id))

    @app.route("/shared")
    @login_required
    def shared_documents():
        current_user_id = flask.session.get("user_id")

        conn = get_db()
        cur = conn.cursor()

        rows = db.get_shared_documents_for_user(cur, current_user_id)

        cur.close()
        conn.close()

        documents = [
            {
                "id": r[0],
                "title": r[1],
                "uploaded_at": r[3],
                "owner_username": r[4],
            }
            for r in rows
        ]

        return flask.render_template(
            "shared.html",
            documents=documents,
            username=flask.session.get("username"),
        )

    @app.route("/shared/<int:document_id>/download")
    @login_required
    def download_shared_document(document_id):
        current_user_id = flask.session.get("user_id")

        conn = get_db()
        cur = conn.cursor()

        row = db.get_shared_document_for_user(cur, document_id, current_user_id)

        cur.close()
        conn.close()

        if not row:
            flask.abort(403)

        conn2 = get_db()
        cur2 = conn2.cursor()
        audit.log_event(cur2, audit.SHARED_DOWNLOAD, user_id=current_user_id,
                        username=flask.session.get("username"),
                        details=f"document_id={document_id}")
        conn2.commit()
        cur2.close()
        conn2.close()

        from app import crypto
        import io

        upload_folder = BASE_DIR / app.config["UPLOAD_FOLDER"]
        filepath = upload_folder / row[3]
        with open(filepath, "rb") as f:
            encrypted = f.read()
        decrypted = crypto.decrypt_file(encrypted)

        return flask.send_file(
            io.BytesIO(decrypted),
            download_name=row[3],
            as_attachment=True,
        )

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
                return flask.redirect(next_url, 307)

            flask.flash("Incorrect password. Please try again.", "error")

        return flask.render_template(
            "admin_confirm_password.html",
            username=flask.session.get("username"),
        )

    @app.route("/admin/users")
    @admin_required
    def admin_users():
        conn = get_db()
        cur = conn.cursor()

        rows = db.get_all_users(cur)

        audit.log_event(cur, audit.ADMIN_USERS_VIEW, user_id=flask.session.get("user_id"),
                        username=flask.session.get("username"))
        conn.commit()
        cur.close()
        conn.close()

        users = [
            {
                "id": r[0],
                "username": r[1],
                "is_disabled": r[2],
                "role": r[3],
            }
            for r in rows
        ]

        return flask.render_template(
            "users.html",
            users=users,
            current_user_id=flask.session.get("user_id"),
            username=flask.session.get("username"),
        )

    @app.route("/admin/users/<int:user_id>/disable", methods=["POST"])
    @admin_required
    @sudo_required
    def admin_disable_user(user_id):
        conn = get_db()
        cur = conn.cursor()

        db.set_user_disabled(cur, user_id, True)
        audit.log_event(cur, audit.ADMIN_USER_DISABLE, user_id=flask.session.get("user_id"),
                        username=flask.session.get("username"),
                        details=f"target_user_id={user_id}")
        conn.commit()
        cur.close()
        conn.close()

        return flask.redirect(flask.url_for("admin_users"))

    @app.route("/admin/users/<int:user_id>/enable", methods=["POST"])
    @admin_required
    @sudo_required
    def admin_enable_user(user_id):
        conn = get_db()
        cur = conn.cursor()

        db.set_user_disabled(cur, user_id, False)
        audit.log_event(cur, audit.ADMIN_USER_ENABLE, user_id=flask.session.get("user_id"),
                        username=flask.session.get("username"),
                        details=f"target_user_id={user_id}")
        conn.commit()
        cur.close()
        conn.close()

        return flask.redirect(flask.url_for("admin_users"))