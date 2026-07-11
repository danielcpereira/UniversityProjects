#!/bin/bash

# -----------------------------------------------------------------------------
# @autor: apbento
#
# This document holds some Kafka, Zookeeper and Postgres useful commands
# -----------------------------------------------------------------------------

# --- Kafka ---

# Runs one producer connected to the bootstrap-server broker1:9092
kafka-console-producer.sh --bootstrap-server broker1:9092 --topic test_topic

# Runs one consumer connected to the bootstrap-server broker1:9092
kafka-console-consumer.sh --bootstrap-server broker1:9092 --topic test_topic

# Runs one consumer that reads all historical data from the beginning
kafka-console-consumer.sh --bootstrap-server broker1:9092 --topic test_topic --from-beginning

# Create one topic with 3 partitions
kafka-topics.sh --bootstrap-server broker1:9092 --create --topic test_topic_with_partitions --partitions 3
kafka-console-producer.sh --bootstrap-server broker1:9092 --topic test_topic_with_partitions
kafka-console-consumer.sh --bootstrap-server broker1:9092 --topic test_topic_with_partitions

# Describe a given topic
kafka-topics.sh --bootstrap-server broker1:9092 --describe --topic test_topic_with_partitions

# List topics
kafka-topics.sh --bootstrap-server broker1:9092 --list

# Delete topic
kafka-topics.sh --bootstrap-server broker1:9092 --delete --topic topic_to_delete

# Delete all topics
kafka-topics.sh --bootstrap-server broker1:9092 --delete --topic ".*"

# Test the performance of Kafka
kafka-producer-perf-test.sh --topic test --num-records 10000 --throughput -1 --producer-props bootstrap.servers=broker1:9092 batch.size=1000 acks=1 linger.ms=50 buffer.memory=4294967296 compression.type=none request.timeout.ms=300000 --record-size 1000

# Schema examples for Kafka producer
#{"schema":{"type":"struct","fields":[{"type":"int32","optional":false,"field":"supplier_id"},{"type":"string","optional":false,"field":"supplier_name"}],"optional":false},"payload":{"supplier_id":1,"supplier_name":"Supplier A"}}

# Schema examples for Kafka producer with a schema composed by string:id and string:value
kafka-console-producer.sh --bootstrap-server INTERNAL://broker1:9092 --topic CountTempReadingsPerWeatherStationTopic # example for exercise 1
#{"schema":{"type":"struct","fields":[{"type":"string","optional":false,"field":"id"},{"type":"string","optional":false,"field":"value"}],"optional":false},"payload":{"id":"1","value":"10"}}
#{"schema":{"type":"struct","fields":[{"type":"string","optional":false,"field":"id"},{"type":"string","optional":false,"field":"value"}],"optional":false},"payload":{"id":"2","value":"20"}}
#{"schema":{"type":"struct","fields":[{"type":"string","optional":false,"field":"id"},{"type":"string","optional":false,"field":"value"}],"optional":false},"payload":{"id":"2","value":"30"}}


# --- Zookeper ---

zookeeper-shell.sh zookeeper:32181
ls /brokers/ids

# --- Postgresql ---

psql -h postgres -p 5432 -U postgres # Login with user postgres
\l               # List databases
\c project3      # Conncet to project3 database
\dt              # List tables
