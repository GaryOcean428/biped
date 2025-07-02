#!/bin/bash
set -e

echo "🚀 Starting Biped Platform..."
echo "📍 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"
echo "🔌 Port: ${PORT:-8080}"
echo "📁 Contents: $(ls -la)"

# Ensure we're in the right directory
cd /app/backend || cd backend || {
    echo "❌ Error: Cannot find backend directory"
    exit 1
}

echo "✅ Changed to backend directory: $(pwd)"
echo "📂 Backend contents: $(ls -la)"

# Start the application with proper port handling
PORT=${PORT:-8080}
echo "🎯 Starting gunicorn on port $PORT..."

exec python -m gunicorn \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    src.main:app

