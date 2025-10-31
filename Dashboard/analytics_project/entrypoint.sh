#!/usr/bin/env bash
set -e

echo "Entry point: waiting for dependent services..."

HOST=${DB_HOST:-db}
PORT=${DB_PORT:-5432}
REDIS_HOST=${REDIS_HOST:-redis}
REDIS_PORT=${REDIS_PORT:-6379}

wait_for_tcp() {
  local host="$1"; local port="$2"
  echo "Waiting for $host:$port..."
  while ! (echo > /dev/tcp/${host}/${port}) >/dev/null 2>&1; do
    echo "  $host:$port not available yet — sleeping 1s"
    sleep 1
  done
  echo "$host:$port is available"
}

# Wait for Postgres
wait_for_tcp "$HOST" "$PORT"
# Wait for Redis
wait_for_tcp "$REDIS_HOST" "$REDIS_PORT"

echo "All dependencies are available — executing command"
exec "$@"
