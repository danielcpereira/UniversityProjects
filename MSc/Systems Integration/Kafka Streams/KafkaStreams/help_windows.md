# Cinema Streaming Platform — IS/EAI 2025/26 (Windows)

> ⚠️ Todos os comandos correm a partir de `~\Documents\GitHub\KafkaStreams\.devcontainer`

---

## 1. Arrancar os containers

```powershell
docker compose -f docker-compose-cluster.yml up -d
```

⏳ Aguarda 3-4 minutos pelo Kafka Connect. Verifica:

```powershell
docker compose -f docker-compose-cluster.yml logs connect --tail=3
```

✅ Continua quando vires: `Herder started`

---

## 2. Compilar

```powershell
cd KafkaStreams
mvn clean package -q
cd .devcontainer
```

---

## 3. Criar tabelas (só na primeira vez)

```powershell
Get-Content ../sql/create_tables.sql | docker compose -f docker-compose-cluster.yml exec -T database psql -U postgres -d project3
```

---

## 4. Registar connectors

**Source connector:**
```powershell
docker compose -f docker-compose-cluster.yml exec connect bash -c "cd /config && curl -X POST -H 'Content-Type: application/json' --data @source.json http://localhost:8083/connectors"
```

**Sink connector:**
```powershell
docker compose -f docker-compose-cluster.yml exec connect bash -c "cd /config && curl -X POST -H 'Content-Type: application/json' --data @sink.json http://localhost:8083/connectors"
```

---

## 5. Arrancar os 4 processos (terminais separados)

**Terminal 1 — Rentals Producer:**
```powershell
docker compose -f docker-compose-cluster.yml exec command-line mvn exec:java "-Dexec.mainClass=cinema.producer.RentalsProducer"
```

**Terminal 2 — Licensing Producer:**
```powershell
docker compose -f docker-compose-cluster.yml exec command-line mvn exec:java "-Dexec.mainClass=cinema.producer.LicensingProducer"
```

⏳ Aguarda 10 segundos até veres eventos nos terminais 1 e 2.

**Terminal 3 — Kafka Streams:**
```powershell
docker compose -f docker-compose-cluster.yml exec command-line mvn exec:java "-Dexec.mainClass=cinema.streams.CinemaStreamsApp"
```

**Terminal 4 — REST Server:**
```powershell
docker compose -f docker-compose-cluster.yml exec command-line mvn exec:java "-Dexec.mainClass=cinema.rest.RestServer"
```

---

## 6. Verificar

```powershell
curl.exe -s http://localhost:7777/stats/revenue-per-film
curl.exe -s http://localhost:7777/stats/profit-per-film
curl.exe -s http://localhost:7777/stats/highest-profit-film
curl.exe -s http://localhost:7777/genres
```

---

## 7. CLI

```powershell
docker compose -f docker-compose-cluster.yml exec command-line mvn exec:java "-Dexec.mainClass=cinema.cli.AdminCLI"
```

---

## 8. Fault Tolerance

```powershell
# Ver brokers ativos
docker compose -f docker-compose-cluster.yml ps | Select-String "broker"

# Ver leaders e replicas
docker compose -f docker-compose-cluster.yml exec broker1 bash -c "kafka-topics --bootstrap-server localhost:9092 --describe --topic CinemaLicensingTopic"

# Matar 2 brokers
docker stop devcontainer-broker2-1
docker stop devcontainer-broker3-1

# Sistema continua a funcionar
curl.exe -s http://localhost:7777/stats/revenue-per-film

# Reiniciar
docker start devcontainer-broker2-1
docker start devcontainer-broker3-1
```

---

## 9. Balanceamento de leaders

```powershell
# Forçar rebalanceamento
docker compose -f docker-compose-cluster.yml exec broker1 bash -c "kafka-leader-election --bootstrap-server localhost:9092 --election-type preferred --all-topic-partitions"

# Verificar
docker compose -f docker-compose-cluster.yml exec broker1 bash -c "kafka-topics --bootstrap-server localhost:9092 --describe --topic CinemaLicensingTopic"
```

---

## Problemas comuns

| Problema | Solução |
|---|---|
| `service "connect" is not running` | Aguarda mais 2-3 min e verifica os logs |
| `ClassNotFoundException` | Faz `mvn clean package -q` antes de arrancar |
| `Unable to initialize state` | `docker compose exec command-line bash -c "kill -9 $(pgrep -f cinema); rm -rf /tmp/kafka-streams"` |
| Porta já em uso | Altera a porta no `docker-compose-cluster.yml` |
| Tabelas vazias | Repete o Passo 3 |
| Sink connector FAILED | Verifica se as tabelas existem com `\dt` no psql |

---

## Tabelas nomes

```powershell
docker compose -f docker-compose-cluster.yml exec database psql -U postgres -d project3 -c "
ALTER TABLE revenue_per_film RENAME TO `"CinemaRevenuePerFilm`";
ALTER TABLE expenses_per_film RENAME TO `"CinemaExpensesPerFilm`";
ALTER TABLE profit_per_film RENAME TO `"CinemaProfitPerFilm`";
ALTER TABLE total_revenue RENAME TO `"CinemaTotalRevenue`";
ALTER TABLE total_expenses RENAME TO `"CinemaTotalExpenses`";
ALTER TABLE total_profit RENAME TO `"CinemaTotalProfit`";
ALTER TABLE avg_transaction_per_film RENAME TO `"CinemaAvgTransactionPerFilm`";
ALTER TABLE avg_transaction_all_films RENAME TO `"CinemaAvgTransactionAllFilms`";
ALTER TABLE highest_profit_film RENAME TO `"CinemaHighestProfitFilm`";
ALTER TABLE revenue_last_hour RENAME TO `"CinemaRevenueLastHour`";
ALTER TABLE expenses_last_hour RENAME TO `"CinemaExpensesLastHour`";
ALTER TABLE profit_last_hour RENAME TO `"CinemaProfitLastHour`";
ALTER TABLE top_genre_per_film RENAME TO `"CinemaTopGenrePerFilm`";
"
```
