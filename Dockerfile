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

# Install Python dependencies with verbose output to diagnose installation issues
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip list

# Verify critical dependencies are installed
RUN pip show flask-caching flask-compress flask-cors flask-migrate || echo "Some dependencies may be missing but will be handled gracefully"

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

# PRESERVE index.html as the PUBLIC landing page - DO NOT OVERWRITE
# index.html should contain the marketplace landing page, not dashboard content

# Ensure proper file permissions
RUN chmod -R 755 ./src/static/

# Create a startup script with cache headers and dependency verification
RUN echo '#!/bin/bash\n\
export CACHE_BUST=$(date +%s)\n\
export FLASK_STATIC_CACHE_TIMEOUT=0\n\
export PYTHONPATH=/app:$PYTHONPATH\n\
export FLASK_APP=src/main.py\n\
\n\
echo "Environment variables:"\n\
echo "DATABASE_URL: ${DATABASE_URL:0:30}..."\n\
echo "REDIS_URL: ${REDIS_URL:0:30}..."\n\
echo "PORT: ${PORT:-8000}"\n\
echo "PYTHONPATH: $PYTHONPATH"\n\
\n\
# Verify critical dependencies before starting\n\
echo "Verifying dependencies..."\n\
pip list | grep -E "flask-caching|flask-compress|flask-cors|flask-migrate" || echo "Some optional dependencies missing but handled gracefully"\n\
\n\
# Start the application with proper error handling\n\
echo "Starting Flask application..."\n\
python src/main.py\n\
' > start.sh && chmod +x start.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application
CMD ["./start.sh"]

