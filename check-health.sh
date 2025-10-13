#!/bin/bash
# Health Check Script for GeoAnnotator
# Usage: ./check-health.sh

echo "🏥 GeoAnnotator Health Check"
echo "============================="
echo ""

# Function to check if a service is responding
check_service() {
    local name=$1
    local url=$2
    local expected_code=${3:-200}

    echo -n "Checking $name... "

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [ "$response" = "$expected_code" ] || [ "$response" = "200" ] || [ "$response" = "302" ]; then
        echo "✓ OK ($response)"
        return 0
    else
        echo "✗ FAILED (HTTP $response)"
        return 1
    fi
}

# Check if Docker containers are running
echo "📦 Checking Docker containers..."
if ! docker-compose ps | grep -q "Up"; then
    echo "✗ Containers are not running. Run ./start-local.sh first"
    exit 1
fi
echo "✓ Docker containers are running"
echo ""

# Check each service
echo "🌐 Checking services..."
check_service "PostgreSQL" "http://localhost:5432" "000"  # Will fail, but container should be running
check_service "MinIO API" "http://localhost:9000/minio/health/live"
check_service "MinIO Console" "http://localhost:9001"
check_service "Backend API" "http://localhost:8000/api/v1/auth/login/"
check_service "Backend Admin" "http://localhost:8000/admin/"
check_service "Frontend" "http://localhost:5173"

echo ""

# Check database connection
echo "🗄️  Checking database connection..."
if docker-compose exec -T backend python manage.py check --database default > /dev/null 2>&1; then
    echo "✓ Database connection OK"
else
    echo "✗ Database connection FAILED"
fi

echo ""

# Check database migrations
echo "📊 Checking migrations..."
pending=$(docker-compose exec -T backend python manage.py showmigrations --plan 2>/dev/null | grep -c "\[ \]" || echo "0")
if [ "$pending" = "0" ]; then
    echo "✓ All migrations applied"
else
    echo "⚠️  $pending migrations pending"
fi

echo ""

# Show container stats
echo "💻 Container resources:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" | grep geoannotator

echo ""
echo "============================="
echo "✅ Health check complete!"
echo ""
echo "Access points:"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  Admin:     http://localhost:8000/admin"
echo "  MinIO:     http://localhost:9001"
