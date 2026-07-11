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