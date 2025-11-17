#!/bin/bash

# Script de vérification de la configuration Celery + Redis
# Usage: ./check-celery-redis.sh

set -e

echo "=========================================="
echo "GeoAnnotator - Celery & Redis Check"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher le résultat
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Fonction pour afficher un warning
warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 1. Vérifier si Redis est installé
echo "1. Checking Redis installation..."
if command -v redis-cli &> /dev/null; then
    check_result 0 "redis-cli is installed"
    REDIS_VERSION=$(redis-cli --version | awk '{print $2}')
    echo "   Version: $REDIS_VERSION"
else
    check_result 1 "redis-cli is not installed"
    warning "Install Redis: sudo apt install redis-server (Ubuntu/Debian)"
fi
echo ""

# 2. Vérifier si Redis est accessible
echo "2. Checking Redis connection..."
if redis-cli ping &> /dev/null; then
    check_result 0 "Redis is running and accessible"

    # Informations Redis
    echo "   Redis info:"
    redis-cli INFO | grep -E "redis_version|used_memory_human|connected_clients" | sed 's/^/   /'
else
    check_result 1 "Cannot connect to Redis"

    # Vérifier si c'est Docker
    if docker ps | grep -q "redis"; then
        warning "Redis is running in Docker. Use: docker-compose exec redis redis-cli ping"
    else
        warning "Start Redis: sudo systemctl start redis"
    fi
fi
echo ""

# 3. Vérifier les variables d'environnement
echo "3. Checking environment variables..."
if [ -f .env ]; then
    check_result 0 ".env file found"

    if grep -q "CELERY_BROKER_URL" .env; then
        BROKER_URL=$(grep "CELERY_BROKER_URL" .env | cut -d'=' -f2)
        echo "   CELERY_BROKER_URL: $BROKER_URL"
    else
        check_result 1 "CELERY_BROKER_URL not found in .env"
    fi

    if grep -q "CELERY_RESULT_BACKEND" .env; then
        RESULT_BACKEND=$(grep "CELERY_RESULT_BACKEND" .env | cut -d'=' -f2)
        echo "   CELERY_RESULT_BACKEND: $RESULT_BACKEND"
    else
        check_result 1 "CELERY_RESULT_BACKEND not found in .env"
    fi
else
    check_result 1 ".env file not found"
    warning "Create .env file with CELERY_BROKER_URL and CELERY_RESULT_BACKEND"
fi
echo ""

# 4. Vérifier si Celery est installé
echo "4. Checking Celery installation..."
cd backend 2>/dev/null || cd .

if [ -f "venv/bin/celery" ]; then
    check_result 0 "Celery is installed (venv)"
    CELERY_VERSION=$(venv/bin/celery --version)
    echo "   Version: $CELERY_VERSION"
elif command -v celery &> /dev/null; then
    check_result 0 "Celery is installed (system)"
    CELERY_VERSION=$(celery --version)
    echo "   Version: $CELERY_VERSION"
else
    check_result 1 "Celery is not installed"
    warning "Install Celery: pip install celery[redis]"
fi
echo ""

# 5. Vérifier les processus Celery
echo "5. Checking Celery processes..."

# Worker
if pgrep -f "celery.*worker" > /dev/null; then
    check_result 0 "Celery worker is running"
    echo "   PIDs: $(pgrep -f 'celery.*worker' | tr '\n' ' ')"
elif docker ps | grep -q "celery_worker"; then
    check_result 0 "Celery worker is running (Docker)"
else
    check_result 1 "Celery worker is not running"
    warning "Start worker: celery -A config worker --loglevel=info"
fi

# Beat
if pgrep -f "celery.*beat" > /dev/null; then
    check_result 0 "Celery beat is running"
    echo "   PIDs: $(pgrep -f 'celery.*beat' | tr '\n' ' ')"
elif docker ps | grep -q "celery_beat"; then
    check_result 0 "Celery beat is running (Docker)"
else
    check_result 1 "Celery beat is not running"
    warning "Start beat: celery -A config beat --loglevel=info"
fi
echo ""

# 6. Vérifier les tâches enregistrées (si Celery est accessible)
echo "6. Checking registered tasks..."
if command -v celery &> /dev/null && [ -f "config/celery.py" ]; then
    TASKS=$(celery -A config inspect registered 2>/dev/null | grep -E "send_email_async|cleanup" || echo "")
    if [ -n "$TASKS" ]; then
        check_result 0 "Celery tasks are registered"
        echo "$TASKS" | sed 's/^/   /'
    else
        warning "Cannot inspect tasks (worker might not be running)"
    fi
elif docker ps | grep -q "celery_worker"; then
    check_result 0 "Celery is running in Docker"
    echo "   Check tasks: docker-compose exec celery_worker celery -A config inspect registered"
else
    warning "Cannot check tasks (Celery not running)"
fi
echo ""

# 7. Résumé
echo "=========================================="
echo "Summary"
echo "=========================================="

if redis-cli ping &> /dev/null && (pgrep -f "celery.*worker" > /dev/null || docker ps | grep -q "celery_worker"); then
    echo -e "${GREEN}✓ System is ready for asynchronous email sending${NC}"
    echo ""
    echo "Next steps:"
    echo "  - Test email sending (register a new user)"
    echo "  - Check Celery logs: docker-compose logs -f celery_worker"
    echo "  or: tail -f /var/log/geoannotator/celery-worker.log"
else
    echo -e "${RED}✗ System is NOT ready${NC}"
    echo ""
    echo "Emails will be sent synchronously (blocking) which may cause timeouts."
    echo ""
    echo "To fix this, you need:"

    if ! redis-cli ping &> /dev/null; then
        echo "  1. Start Redis: sudo systemctl start redis"
        echo "     or: docker-compose up -d redis"
    fi

    if ! pgrep -f "celery.*worker" > /dev/null && ! docker ps | grep -q "celery_worker"; then
        echo "  2. Start Celery worker: celery -A config worker --loglevel=info"
        echo "     or: docker-compose up -d celery_worker"
    fi

    if ! pgrep -f "celery.*beat" > /dev/null && ! docker ps | grep -q "celery_beat"; then
        echo "  3. Start Celery beat: celery -A config beat --loglevel=info"
        echo "     or: docker-compose up -d celery_beat"
    fi

    echo ""
    echo "For detailed setup instructions, see: docs/celery-redis-setup.md"
fi

echo ""
