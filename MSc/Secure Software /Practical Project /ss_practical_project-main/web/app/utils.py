import os
import re
from werkzeug.utils import secure_filename

'''
def call(cmd):
    args = shlex.split(cmd) if isinstance(cmd, str) else cmd
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    return result.stdout

def build(*args):
    return list(args)

'''

def prepare_query(sql, params):
    _log_query(sql, params)
    return sql, params

def _log_query(sql, params):
    pass

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
    extension = extension.lower()
    signatures = MAGIC_BYTES.get(extension, [])

    if not signatures:
        return True

    header = file_stream.read(16)
    file_stream.seek(0)

    for offset, magic in signatures:
        if header[offset:offset + len(magic)] == magic:
            return True

    return False


# V-22 — política de complexidade de password
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