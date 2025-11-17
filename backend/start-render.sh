#!/bin/bash
# Render.com startup script - Runs Django + Celery in single container
# This allows using only 1 free web service instead of 3 separate services

set -e

echo "Starting GeoAnnotator services..."

# Start Celery Worker in background
echo "Starting Celery Worker..."
celery -A config worker --loglevel=info --concurrency=2 &
CELERY_WORKER_PID=$!

# Start Celery Beat in background
echo "Starting Celery Beat..."
celery -A config beat --loglevel=info &
CELERY_BEAT_PID=$!

# Give Celery services time to start
sleep 5

# Start Gunicorn in foreground (must be foreground for Render to monitor)
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:10000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

# Note: When Gunicorn exits, the container stops and Celery processes are killed
# This is fine for Render's model
