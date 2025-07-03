# Single-stage Dockerfile for Biped Platform with cache clearing
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

# DO NOT copy frontend build to prevent conflicts
# The static directory already contains the correct HTML files

# Remove any React build artifacts that might cause conflicts
RUN find ./src/static/ -name "main.*.css" -delete || true && \
    find ./src/static/ -name "main.*.js" -delete || true && \
    find ./src/static/ -name "*.chunk.js" -delete || true && \
    find ./src/static/ -name "manifest.json" -delete || true && \
    find ./src/static/ -name "favicon.ico" -delete || true && \
    find ./src/static/ -name "logo*.png" -delete || true

# Ensure index.html contains the correct dashboard content
RUN if [ -f ./src/static/dashboard-enhanced.html ]; then \
        cp ./src/static/dashboard-enhanced.html ./src/static/index.html; \
    elif [ -f ./src/static/dashboard.html ]; then \
        cp ./src/static/dashboard.html ./src/static/index.html; \
    fi

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

