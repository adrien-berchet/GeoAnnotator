#!/bin/bash
# GeoAnnotator Stop Script
# Usage: ./stop-local.sh [--clean]

echo "🛑 Stopping GeoAnnotator..."
echo ""

if [ "$1" = "--clean" ]; then
    echo "⚠️  Clean mode: This will remove all data (database, media files)"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        echo "✓ Services stopped and volumes removed"
    else
        echo "Cancelled"
        exit 0
    fi
else
    docker-compose down
    echo "✓ Services stopped (data preserved)"
fi

echo ""
echo "To start again: ./start-local.sh"
