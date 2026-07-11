#!/bin/bash
# Post all Kafka Connect connectors
CONNECT_URL="http://connect:8083/connectors"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Posting source connector (films)..."
curl -s -X POST -H "Content-Type: application/json" \
     --data @"$SCRIPT_DIR/source.json" "$CONNECT_URL" | jq .

echo "Posting source connector (genres)..."
curl -s -X POST -H "Content-Type: application/json" \
     --data @"$SCRIPT_DIR/source_genres.json" "$CONNECT_URL" | jq .

echo "Posting sink connector..."
curl -s -X POST -H "Content-Type: application/json" \
     --data @"$SCRIPT_DIR/sink.json" "$CONNECT_URL" | jq .

echo "Done. Current connectors:"
curl -s "$CONNECT_URL" | jq .
