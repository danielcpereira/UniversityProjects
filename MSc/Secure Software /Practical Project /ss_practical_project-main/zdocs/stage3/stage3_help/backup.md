# Forçar um backup imediato
docker compose exec db-backup /scripts/backup.sh

# Ver backups disponíveis
docker compose exec db-backup ls -lh /backups/data/

# Restaurar um backup específico
docker compose exec db-backup /scripts/restore.sh /backups/data/pgbackup_20260509_030000.dump