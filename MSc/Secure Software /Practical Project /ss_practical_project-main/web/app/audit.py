import datetime
import logging
import flask


# Eventos para os quais o IP tem relevância de segurança e deve ser registado.
# Para todos os outros eventos o IP não é armazenado (data minimization).
_EVENTS_REQUIRING_IP = frozenset({
    "login_success",
    "login_failure",
    "logout",
})


def log_event(cur, event_type, user_id=None, username=None, details=None):
    """
    Regista um evento de segurança na tabela audit_logs.

    Parâmetros:
        cur        — cursor psycopg2 já aberto (a chamada não faz commit)
        event_type — string identificadora do evento (ver constantes abaixo)
        user_id    — id do utilizador que originou o evento (pode ser None)
        username   — username do utilizador (útil quando o login falha e não há id)
        details    — texto livre com contexto adicional (ex: document_id, target_user)

    Política de data minimization:
        O IP do cliente só é registado para eventos de autenticação
        (_EVENTS_REQUIRING_IP). Para eventos de acesso a documentos e ações
        administrativas o IP não é armazenado — o user_id é suficiente para
        rastreabilidade e o IP não acrescenta valor probatório nesse contexto.
    """
    ip_address = None
    if event_type in _EVENTS_REQUIRING_IP:
        try:
            ip_address = flask.request.remote_addr
        except RuntimeError:
            pass  # fora de contexto de request (ex: testes)

    cur.execute(
        """
        INSERT INTO audit_logs (event_type, user_id, username, ip_address, details, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            event_type,
            user_id,
            username,
            ip_address,
            details,
            datetime.datetime.now(datetime.timezone.utc),
        ),
    )


# ---------------------------------------------------------------------------
# Constantes para event_type — usar sempre estas strings para consistência
# ---------------------------------------------------------------------------

# Autenticação
LOGIN_SUCCESS   = "login_success"
LOGIN_FAILURE   = "login_failure"
LOGOUT          = "logout"

# Documentos
DOCUMENT_UPLOAD   = "document_upload"
DOCUMENT_DOWNLOAD = "document_download"
DOCUMENT_VIEW     = "document_view"
DOCUMENT_SHARE    = "document_share"

# Documentos partilhados
SHARED_DOWNLOAD = "shared_document_download"

# Ações administrativas
ADMIN_USER_DISABLE = "admin_user_disable"
ADMIN_USER_ENABLE  = "admin_user_enable"
ADMIN_USERS_VIEW   = "admin_users_view"

# V-33 — acesso negado (para deteção de anomalias)
ACCESS_DENIED      = "access_denied"

# ---------------------------------------------------------------------------
# V-33 — Deteção de atividade suspeita (SR-25)
# ---------------------------------------------------------------------------

_security_logger = logging.getLogger("security")

# Thresholds configuráveis
FAILED_LOGIN_WINDOW_SECONDS  = 300   # janela de 5 minutos
FAILED_LOGIN_THRESHOLD       = 5     # nº de falhas que dispara alerta
ACCESS_DENIED_WINDOW_SECONDS = 120   # janela de 2 minutos
ACCESS_DENIED_THRESHOLD      = 10    # nº de acessos negados que dispara alerta


def check_suspicious_activity(cur, event_type, user_id=None, username=None, ip_address=None):
    """
    Analisa os audit logs recentes e deteta padrões suspeitos.

    Padrões detetados:
      - LOGIN_FAILURE  : muitas falhas de login seguidas para o mesmo IP ou username
                         (indicador de brute-force / credential stuffing)
      - ACCESS_DENIED  : muitos acessos negados em série para o mesmo utilizador
                         (indicador de enumeração de recursos ou IDOR automatizado)

    Quando um threshold é ultrapassado:
      1. Emite um WARNING no logger "security" (visível nos logs do container).
      2. Regista um evento "suspicious_activity" nos audit_logs para auditoria.

    Deve ser chamada DEPOIS de log_event, com o mesmo cursor (sem commit intermédio).
    """
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