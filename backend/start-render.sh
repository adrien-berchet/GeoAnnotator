#!/bin/bash
# Render.com startup script - Runs Django + Celery in single container
# This allows using only 1 free web service instead of 3 separate services

set -e

echo "============================================================"
echo "Starting GeoAnnotator services..."
echo "============================================================"

# Display email configuration
echo ""
echo "📧 EMAIL CONFIGURATION CHECK"
echo "------------------------------------------------------------"
python << 'EOF'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
import django
django.setup()
from django.conf import settings

backend = settings.EMAIL_BACKEND
print(f"Email Backend: {backend}")

if "mailjet" in backend.lower():
    api_key = getattr(settings, "MAILJET_API_KEY", None)
    secret_key = getattr(settings, "MAILJET_SECRET_KEY", None)
    print(f"Backend Type: Mailjet HTTP API")
    print(f"API Key Configured: {bool(api_key)}")
    print(f"Secret Key Configured: {bool(secret_key)}")
    if api_key:
        print(f"API Key Preview: {api_key[:8]}...")
    print(f"Default From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
    print(f"Default From Name: {getattr(settings, 'DEFAULT_FROM_NAME', 'Not set')}")
    if api_key and secret_key:
        print("Status: ✅ CONFIGURED")
    else:
        print("Status: ❌ MISSING CREDENTIALS")
elif "smtp" in backend.lower():
    print(f"Backend Type: SMTP")
    print(f"SMTP Host: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
    print(f"SMTP Port: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
else:
    print(f"Backend Type: {backend}")
EOF
echo "============================================================"
echo ""

# Start Celery Worker in background
# Using solo pool (single process) to minimize Redis queries
# Disabled: gossip, mingle, heartbeat - these cause extra Redis traffic
echo "🔄 Starting Celery Worker..."
celery -A config worker \
    --loglevel=info \
    --pool=solo \
    --without-gossip \
    --without-mingle \
    --without-heartbeat \
    &
CELERY_WORKER_PID=$!

# Start Celery Beat in background
echo "⏰ Starting Celery Beat..."
celery -A config beat --loglevel=info &
CELERY_BEAT_PID=$!

# Give Celery services time to start
sleep 5

# Start Gunicorn in foreground (must be foreground for Render to monitor)
echo "🚀 Starting Gunicorn..."
echo ""
exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:10000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

# Note: When Gunicorn exits, the container stops and Celery processes are killed
# This is fine for Render's model
