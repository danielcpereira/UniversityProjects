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