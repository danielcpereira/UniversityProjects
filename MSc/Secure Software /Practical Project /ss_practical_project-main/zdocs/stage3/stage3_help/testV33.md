# Teste V-33 — Deteção de Atividade Suspeita

## Pré-requisitos
```bash
docker compose up -d
```

---

## Teste 1 — Brute-force no login

```bash
# 1. Obter token CSRF
TOKEN=$(curl -s http://localhost:8000/login -c /tmp/cookies.txt | grep csrf_token | sed 's/.*value="\([^"]*\)".*/\1/')

# 2. Disparar 6 logins falhados
for i in $(seq 1 6); do
  curl -s -X POST http://localhost:8000/login \
    -d "username=alice&password=errada&csrf_token=$TOKEN" \
    -c /tmp/cookies.txt -b /tmp/cookies.txt -L > /dev/null
  echo "Tentativa $i"
done
```

### Verificar resultado

```bash
# Logs do container
docker logs ss_practical_project-web-1 2>&1 | grep "SUSPICIOUS"

# Registo na BD
docker exec -it ss_practical_project-db-1 psql -U postgres -d docdb \
  -c "SELECT event_type, username, details, created_at FROM audit_logs WHERE event_type = 'suspicious_activity' ORDER BY created_at DESC LIMIT 5;"
```

### Resultado esperado
- Log: `WARNING security: [SUSPICIOUS ACTIVITY] Brute-force detetado: ...`
- BD: registo com `event_type = suspicious_activity`

---

## Teste 2 — Acessos negados repetidos (IDOR)

```bash
# 1. Login como alice
TOKEN=$(curl -s http://localhost:8000/login -c /tmp/alice.txt | grep csrf_token | sed 's/.*value="\([^"]*\)".*/\1/')
curl -s -X POST http://localhost:8000/login \
  -d "username=alice&password=<password_alice>&csrf_token=$TOKEN" \
  -c /tmp/alice.txt -b /tmp/alice.txt -L > /dev/null

# 2. Tentar aceder a 11 documentos alheios
for i in $(seq 1 11); do
  curl -s http://localhost:8000/documents/$i -b /tmp/alice.txt > /dev/null
  echo "Tentativa $i"
done
```

### Verificar resultado

```bash
docker logs ss_practical_project-web-1 2>&1 | grep "SUSPICIOUS"
```

# Ver na base de dados

```
docker exec -it ss_practical_project-db-1 psql -U postgres -d docdb \
  -c "SELECT event_type, username, details, created_at FROM audit_logs WHERE event_type = 'suspicious_activity' ORDER BY created_at DESC;"
```