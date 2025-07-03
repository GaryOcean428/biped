# Multi-stage Dockerfile for Biped Platform with cache clearing
FROM node:18-alpine AS frontend-builder

# Set working directory for frontend
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./
COPY frontend/yarn.lock ./

# Install frontend dependencies with cache clearing
RUN yarn install --frozen-lockfile --network-timeout 300000

# Copy frontend source code
COPY frontend/ ./

# Build frontend with cache busting
ENV GENERATE_SOURCEMAP=false
ENV REACT_APP_CACHE_BUST=$(date +%s)
RUN yarn build

# Python backend stage
FROM python:3.11-slim AS backend-builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FLASK_APP=src/main.py

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./

# Copy frontend build from previous stage
COPY --from=frontend-builder /app/frontend/build ./src/static/

# Create cache-busting index.html with timestamp
RUN CACHE_BUST=$(date +%s) && \
    sed -i "s/\(href=\"[^\"]*\.\(css\|js\)\)/\1?v=${CACHE_BUST}/g" ./src/static/index.html && \
    sed -i "s/\(src=\"[^\"]*\.\(css\|js\)\)/\1?v=${CACHE_BUST}/g" ./src/static/index.html

# Remove any conflicting files that might cause routing issues
RUN find ./src/static/ -name "index-system-status*" -delete || true && \
    find ./src/static/ -name "main.*.css" -delete || true && \
    find ./src/static/ -name "main.*.js" -delete || true

# Ensure proper file permissions
RUN chmod -R 755 ./src/static/

# Create a startup script with cache headers
RUN echo '#!/bin/bash\n\
export CACHE_BUST=$(date +%s)\n\
export FLASK_STATIC_CACHE_TIMEOUT=0\n\
python -m flask run --host=0.0.0.0 --port=${PORT:-8000}\n\
' > start.sh && chmod +x start.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["./start.sh"]

