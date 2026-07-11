from . import utils

def get_user_by_username(cur, username):
    cur.execute(
        "SELECT id, username, password, is_disabled, role FROM users WHERE username = %s",
        (username,)
    )
    return cur.fetchone()

def get_all_users(cur):
    cur.execute(
        "SELECT id, username, is_disabled, role FROM users ORDER BY id"
    )
    return cur.fetchall()

def set_user_disabled(cur, user_id, disabled):
    cur.execute(
        "UPDATE users SET is_disabled = %s WHERE id = %s",
        (disabled, user_id)
    )

def get_user_by_id(cur, user_id):
    cur.execute(
        "SELECT id, username, is_disabled, role FROM users WHERE id = %s",
        (user_id,)
    )
    return cur.fetchone()

def share_document(cur, document_id, owner_id, shared_with_id):
    cur.execute(
        """
        SELECT id FROM document_shares
        WHERE document_id = %s AND shared_with_id = %s
        """,
        (document_id, shared_with_id)
    )
    if cur.fetchone():
        return False
    cur.execute(
        """
        INSERT INTO document_shares (document_id, owner_id, shared_with_id)
        VALUES (%s, %s, %s)
        """,
        (document_id, owner_id, shared_with_id)
    )
    return True

def get_shared_documents_for_user(cur, user_id):
    cur.execute(
        """
        SELECT d.id, d.title, d.filename, d.uploaded_at, u.username AS owner_username
        FROM document_shares ds
        JOIN documents d ON ds.document_id = d.id
        JOIN users u ON d.owner_id = u.id
        WHERE ds.shared_with_id = %s
        ORDER BY d.uploaded_at DESC
        """,
        (user_id,)
    )
    return cur.fetchall()

def get_shared_document_for_user(cur, document_id, user_id):
    """Devolve o documento apenas se foi partilhado com user_id."""
    cur.execute(
        """
        SELECT d.id, d.owner_id, d.title, d.filename
        FROM document_shares ds
        JOIN documents d ON ds.document_id = d.id
        WHERE ds.document_id = %s AND ds.shared_with_id = %s
        """,
        (document_id, user_id)
    )
    return cur.fetchone()

def get_shares_for_document(cur, document_id, owner_id):
    """Lista os utilizadores com quem o dono partilhou o documento."""
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

def revoke_share(cur, document_id, owner_id, shared_with_id):
    """Remove o acesso de um utilizador a um documento do dono."""
    cur.execute(
        """
        DELETE FROM document_shares
        WHERE document_id = %s AND owner_id = %s AND shared_with_id = %s
        """,
        (document_id, owner_id, shared_with_id)
    )
    return cur.rowcount > 0