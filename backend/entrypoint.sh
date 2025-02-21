#!/bin/bash

if [ "$1" = "celery" ]; then
    if [ "$2" = "beat" ]; then
        exec celery -A app.services.celery.celery beat --loglevel=info
    else
        exec celery -A app.services.celery.celery worker --loglevel=info
    fi
else
    exec uvicorn main:app --host 0.0.0.0 --port 8000
fi 