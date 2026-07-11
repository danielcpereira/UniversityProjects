FROM alpine:3.21

RUN apk add --no-cache postgresql17-client

COPY backup.sh /scripts/backup.sh
COPY restore.sh /scripts/restore.sh
RUN chmod +x /scripts/backup.sh /scripts/restore.sh

VOLUME ["/backups"]

CMD ["sh", "-c", "while true; do /scripts/backup.sh; sleep 600; done"]