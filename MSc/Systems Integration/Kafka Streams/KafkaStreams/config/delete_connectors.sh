#!/bin/bash
for name in jdbc-source-films jdbc-source-genres jdbc-cinema-sink; do
    echo "Deleting $name..."
    curl -s -X DELETE "http://connect:8083/connectors/$name"
    echo
done
