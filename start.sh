#!/bin/bash
set -e

echo "Starting Biped Platform..."
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Port: $PORT"

# Ensure we're in the right directory
cd /app/backend || cd backend

# Start the application
exec python -m gunicorn --bind 0.0.0.0:${PORT:-8080} --workers 1 --timeout 120 src.main:app

