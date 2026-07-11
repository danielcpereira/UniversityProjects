-- ---------------------------------------------------------------------------
-- POLÍTICA DE DATA MINIMIZATION
--
-- Princípio: cada coluna armazena apenas o mínimo de informação necessária
-- para o funcionamento da funcionalidade a que serve.
--
-- users:
--   - username   : limitado a 64 caracteres (suficiente para qualquer
--                  identificador prático; evita armazenamento de dados
--                  arbitrariamente longos)
--   - password   : apenas o hash bcrypt — nunca a password em claro
--   - is_disabled, role : campos operacionais mínimos; sem dados de perfil
--                  opcionais (e-mail, nome completo, etc.) que não são
--                  necessários para as funcionalidades implementadas
--
-- documents:
--   - metadata   : apenas size_bytes e extension (ver extract_metadata em
--                  app.py); paths do servidor, inodes e permissões Unix
--                  são deliberadamente excluídos
--
-- audit_logs:
--   - ip_address : registado APENAS para eventos de autenticação
--                  (login_success, login_failure, logout); para eventos de
--                  acesso a documentos e ações administrativas o IP não é
--                  necessário — o user_id garante rastreabilidade suficiente
--   - details    : apenas IDs de referência (document_id, target_user_id);
--                  nunca paths internos do servidor nem conteúdo de ficheiros
-- ---------------------------------------------------------------------------

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password TEXT NOT NULL,
    is_disabled BOOLEAN DEFAULT FALSE,
    role TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin'))
);

CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id),
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    metadata TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_logs (
    id          SERIAL PRIMARY KEY,
    event_type  TEXT NOT NULL,
    user_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    username    TEXT,
    ip_address  TEXT,
    details     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_logs_user_id    ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

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

CREATE TABLE document_shares (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    owner_id INTEGER REFERENCES users(id),
    shared_with_id INTEGER REFERENCES users(id)
);

-- ---------------------------------------------------------------------------
-- IMPORTANT — VALIDATOR ACCOUNTS
--
-- The following user accounts are required for the automated validation
-- system used in the course. These accounts MUST always exist in the system.
--
-- The usernames and logical identities of these accounts must NOT be removed
-- or changed, as the validator depends on them to execute security tests.
--
-- The validator authenticates using the plaintext credentials defined below.
-- Therefore:
--
--  • These credentials must remain valid for authentication.
--  • The passwords themselves must not be changed.
--
-- You are free to improve the authentication system (e.g., password hashing,
-- stronger password policies, etc.). If you implement password hashing or
-- other changes to the login mechanism, ensure that the credentials below
-- still successfully authenticate.
--
-- In other words: the authentication implementation may change, but the
-- following username/password combinations must continue to work.
--
-- These accounts are used by the automated validator to test:
--   • authentication
--   • authorization
--   • document sharing
--   • access control
--   • administrative operations
--
-- Removing or altering these accounts will cause automated validation to fail.
-- ---------------------------------------------------------------------------

INSERT INTO users (username, password, is_disabled, role) VALUES
('admin', '$2b$12$f1J2zBeJCvZbskpELV29bepsMf.protdYaoIK699iLP2Gzi9S8wSW', FALSE, 'admin'),
('alice', '$2b$12$U4EGolt0YWYGC2lPgqwID.ypyukgEfqLjBL0vlVjuowT9gL3mrj2C', FALSE, 'user'),
('bob', '$2b$12$WB7eXC2oyYJCzU.07H/ObOaTEXctefzx1A88kyTBXJvUM9qN9JtIW', FALSE, 'user');