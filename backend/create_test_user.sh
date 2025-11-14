#!/bin/bash
# Quick script to create test users for development
# Usage: ./create_test_user.sh [--verified] [--delete-existing]

cd "$(dirname "$0")"

echo "🚀 GeoAnnotator Test User Creator"
echo ""

python manage.py create_test_user "$@"
