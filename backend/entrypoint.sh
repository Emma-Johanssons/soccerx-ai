#!/bin/bash

set -e

# Wait for Redis to be ready
wait_for_redis() {
    echo "Waiting for Redis..."
    while ! redis-cli -h redis ping; do
        sleep 1
    done
    echo "Redis is ready!"
}

case "$1" in
    "celery-worker")
        echo "Starting Celery worker..."
        wait_for_redis
        celery -A app.base_celery worker --loglevel=info
        ;;
    "celery-beat")
        echo "Starting Celery beat..."
        wait_for_redis
        rm -f ./celerybeat-schedule
        celery -A app.base_celery beat --loglevel=info
        ;;
    "web")
        echo "Starting web server..."
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    *)
        echo "Unknown command: $1"
        exit 1
        ;;
esac