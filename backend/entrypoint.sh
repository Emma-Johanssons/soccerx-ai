#!/bin/sh

case "$1" in
    "celery-worker")
        celery -A app.services.celery worker --loglevel=info
        ;;
    "celery-beat")
        celery -A app.services.celery beat --loglevel=info
        ;;
    "web")
        uvicorn main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    *)
        exec "$@"
        ;;
esac 