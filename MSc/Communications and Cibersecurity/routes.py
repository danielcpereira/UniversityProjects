from flask import Blueprint, request, redirect, url_for, render_template, session
from app import get_db_connection
from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError
import pyotp
import base64
import qrcode
import io
import re
from qrcode.image.pil import PilImage
from app import limiter

bp = Blueprint("main", __name__)
ph = PasswordHasher(type=Type.ID)

#----------------------------#
# INPUT VALIDATION HELPERS
#----------------------------#
def validate_username(username):
    """
    Validate username:
    - Length: 3-32 characters
    - Allowed: alphanumeric, underscore, hyphen
    """
    if not username or not isinstance(username, str):
        return False, "Username é obrigatório"
    
    if len(username) < 3 or len(username) > 32:
        return False, "Username deve ter entre 3 e 32 caracteres"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username só pode conter letras, números, _ e -"
    
    return True, None


def validate_password(password):
    """
    Validate password:
    - Length: 8-128 characters
    - Must contain: uppercase, lowercase, digit, special char
    """
    if not password or not isinstance(password, str):
        return False, "Password é obrigatória"
    
    if len(password) < 8 or len(password) > 128:
        return False, "Password deve ter entre 8 e 128 caracteres"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password deve conter pelo menos uma letra maiúscula"
    
    if not re.search(r'[a-z]', password):
        return False, "Password deve conter pelo menos uma letra minúscula"
    
    if not re.search(r'[0-9]', password):
        return False, "Password deve conter pelo menos um dígito"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password deve conter pelo menos um caractere especial"
    
    return True, None


def validate_otp(otp):
    """
    Validate OTP code:
    - Exactly 6 digits
    """
    if not otp or not isinstance(otp, str):
        return False, "Código OTP é obrigatório"
    
    if not re.match(r'^\d{6}$', otp):
        return False, "Código OTP deve ter exatamente 6 dígitos"
    
    return True, None


#----------------------------#
# SANITIZATION HELPER
#----------------------------#
def sanitize_input(text, max_length=256):
    """
    Sanitize text input:
    - Strip whitespace
    - Limit length
    - Remove null bytes
    """
    if not isinstance(text, str):
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Strip whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text

#----------------------------#
# Home page
#----------------------------#
@bp.route('/')
def index():
    return render_template('index.html')

#----------------------------#
# REGISTER (UPDATED)
#----------------------------#
@bp.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')

@bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    # Get and sanitize inputs
    username = sanitize_input(request.form.get('username', ''), max_length=32)
    password = sanitize_input(request.form.get('password', ''), max_length=128)

    # Validate username
    valid, error = validate_username(username)
    if not valid:
        return render_template("error.html", message=error), 400

    # Validate password
    valid, error = validate_password(password)
    if not valid:
        return render_template("error.html", message=error), 400

    try:
        password_hash = ph.hash(password)
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            return render_template("error.html", message="O utilizador já existe!"), 409

        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash),
        )
        conn.commit()
        cur.close()
        conn.close()

        return render_template("success.html", message="Registo concluído. Agora faz login.")
    except Exception as e:
        return render_template("error.html", message="Erro ao registar utilizador"), 500


#----------------------------#
# LOGIN 
#----------------------------#
@bp.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

@bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Get and sanitize inputs
    username = sanitize_input(request.form.get('username', ''), max_length=32)
    password = sanitize_input(request.form.get('password', ''), max_length=128)

    # Validate username
    valid, error = validate_username(username)
    if not valid:
        return render_template("error.html", message="Credenciais inválidas"), 401

    # Validate password (basic check)
    if not password or len(password) < 8:
        return render_template("error.html", message="Credenciais inválidas"), 401

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, password_hash, twofa_enabled FROM users WHERE username=%s", (username,))
    row = cur.fetchone()

    if not row:
        return render_template("error.html", message="Credenciais inválidas"), 401

    user_id, stored_hash, twofa_enabled = row

    try:
        ph.verify(stored_hash, password)
    except VerifyMismatchError:
        return render_template("error.html", message="Credenciais inválidas"), 401

    session['pending_user'] = user_id

    if twofa_enabled:
        return redirect(url_for('main.twofa_verify_login_form'))
    else:
        session['user_id'] = user_id
        return redirect(url_for('main.dashboard'))

#----------------------------#
# DASHBOARD
#----------------------------#
@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('main.login_form'))

    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT username, twofa_enabled FROM users WHERE id=%s", (user_id,))
    username, twofa_enabled = cur.fetchone()

    return render_template('dashboard.html', username=username, twofa_enabled=twofa_enabled)

#----------------------------#
# SETUP 2FA
#----------------------------#
@bp.route('/2fa/setup')
def twofa_setup():
    if 'user_id' not in session:
        return redirect(url_for('main.login_form'))

    user_id = session['user_id']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT otp_secret FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()

    if row[0] is None:
        secret = pyotp.random_base32()
        cur.execute("UPDATE users SET otp_secret=%s WHERE id=%s", (secret, user_id))
        conn.commit()
    else:
        secret = row[0]

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name="CyberApp", issuer_name="CyberSecurityProject")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(uri)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode()

    return render_template('2fa_setup.html', qr_code=qr_base64)

#----------------------------#
#  CONFIRM 2FA
#----------------------------#
@bp.route('/2fa/verify', methods=['POST'])
def twofa_verify():
    if 'user_id' not in session:
        return redirect(url_for('main.login_form'))

    user_id = session['user_id']
    otp = sanitize_input(request.form.get('otp', ''), max_length=6)

    # Validate OTP
    valid, error = validate_otp(otp)
    if not valid:
        return render_template("error.html", message=error), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT otp_secret FROM users WHERE id=%s", (user_id,))
    secret = cur.fetchone()[0]

    totp = pyotp.TOTP(secret)

    if totp.verify(otp):
        cur.execute("UPDATE users SET twofa_enabled=TRUE WHERE id=%s", (user_id,))
        conn.commit()
        return render_template("success.html", message="2FA ativado com sucesso!")

    return render_template("error.html", message="Código 2FA incorreto"), 401


#----------------------------#
# LOGIN 2FA FORM
#----------------------------#
@bp.route('/2fa/login', methods=['GET'])
def twofa_verify_login_form():
    return render_template('2fa_verify.html')


#----------------------------#
# 2FA LOGIN
#----------------------------#
@bp.route('/2fa/verify-login', methods=['POST'])
def twofa_verify_login():
    if 'pending_user' not in session:
        return redirect(url_for('main.login_form'))

    user_id = session['pending_user']
    otp = sanitize_input(request.form.get('otp', ''), max_length=6)

    # Validate OTP
    valid, error = validate_otp(otp)
    if not valid:
        return render_template("error.html", message=error), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT otp_secret FROM users WHERE id=%s", (user_id,))
    secret = cur.fetchone()[0]

    totp = pyotp.TOTP(secret)

    if totp.verify(otp):
        session['user_id'] = user_id
        session.pop('pending_user')
        return redirect(url_for('main.dashboard'))

    return render_template("error.html", message="Código 2FA inválido"), 401


@bp.route('/ip')
def check_ip():
    return request.remote_addr


#----------------------------#
# LOGOUT
#----------------------------#
@bp.route('/logout')
def logout():
    session.clear()
    return render_template("logout.html")

