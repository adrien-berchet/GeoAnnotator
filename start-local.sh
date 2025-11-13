#!/bin/bash
# GeoAnnotator Local Deployment Script
# Usage: ./start-local.sh

set -e

echo "🚀 GeoAnnotator - Local Deployment"
echo "===================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your settings before continuing"
    exit 1
fi

echo "✓ .env file found"
echo ""

# Clean up any orphaned containers (fixes ContainerConfig error)
echo "🧹 Cleaning up orphaned containers..."
docker-compose down --remove-orphans > /dev/null 2>&1 || true

# Build and start services
echo "🔨 Building Docker images..."
docker-compose build

echo ""
echo "🚢 Starting services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 10

# Wait for database to be healthy
echo "Checking database health..."
until docker-compose exec -T db pg_isready -U geoannotator > /dev/null 2>&1; do
    echo "  Waiting for PostgreSQL..."
    sleep 2
done

echo "✓ Database is ready"
echo ""

# Run migrations
echo "🔄 Running database migrations..."
docker-compose exec -T backend python manage.py migrate --noinput

echo ""
echo "👤 Creating superuser (if needed)..."
echo "from apps.authentication.models import User; User.objects.create_superuser('admin', 'admin@geoannotator.local', 'admin123') if not User.objects.filter(email_hash=User.hash_email('admin@geoannotator.local')).exists() else None" | docker-compose exec -T backend python manage.py shell

echo ""
echo "✅ Deployment complete!"
echo ""
echo "===================================="
echo "📱 Access the application:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   Admin:    http://localhost:8000/admin"
echo "   MinIO:    http://localhost:9001"
echo ""
echo "🔑 Default credentials:"
echo "   Email:    admin@geoannotator.local"
echo "   Password: admin123"
echo ""
echo "📋 Useful commands:"
echo "   View logs:    docker-compose logs -f"
echo "   Stop:         docker-compose down"
echo "   Restart:      docker-compose restart"
echo "   Shell:        docker-compose exec backend python manage.py shell"
echo "===================================="
