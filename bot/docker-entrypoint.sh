#!/bin/bash

# check if all services running
./wait-for-it.sh -t 0 "${MYSQL_HOST}:${MYSQL_PORT}" && echo "MySQL running"
./wait-for-it.sh -t 0 "${RABBITMQ_HOST}:${RABBITMQ_PORT}" && echo "RabbitMQ running"
./wait-for-it.sh -t 0 "${BACKEND_HOST:-supportbot_backend}:${BACKEND_PORT:-80}" && echo "Backend running"

python main.py