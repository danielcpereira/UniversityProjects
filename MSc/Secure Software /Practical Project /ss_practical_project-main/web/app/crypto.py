import os
from cryptography.fernet import Fernet

def get_fernet() -> Fernet:
    """
    Lê a chave de cifra da variável de ambiente FILE_ENCRYPTION_KEY.
    Falha explicitamente se não estiver definida — nunca usa fallback.
    """
    key = os.getenv("FILE_ENCRYPTION_KEY")
    if not key:
        raise RuntimeError("FILE_ENCRYPTION_KEY não está definida")
    return Fernet(key.encode())


def encrypt_file(data: bytes) -> bytes:
    """Cifra os bytes de um ficheiro. Devolve os bytes cifrados."""
    return get_fernet().encrypt(data)


def decrypt_file(data: bytes) -> bytes:
    """Decifra os bytes de um ficheiro. Devolve os bytes originais."""
    return get_fernet().decrypt(data)