# Railway-Optimized Dockerfile for Biped Platform
# Single service architecture serving Flask backend + React frontend

FROM node:20-slim AS frontend-builder

# Set working directory for frontend build
WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install frontend dependencies with npm (including dev dependencies for build)
RUN npm install

# Copy frontend source code
COPY frontend/ ./

# Build React frontend for production
RUN npm run build

# Production stage with Python
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Install essential system dependencies only
RUN apt-get update && apt-get install -y \
    # Essential build tools
    build-essential \
    pkg-config \
    curl \
    # PostgreSQL client
    libpq-dev \
    # OpenCV headless dependencies (minimal)
    libglib2.0-0 \
    libgomp1 \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create data directory for Railway volume
RUN mkdir -p /data && chmod 755 /data

# Copy requirements first for better layer caching
COPY backend/requirements.txt ./backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Copy backend application code
COPY backend/ ./backend/

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build/ ./backend/src/static/

# Set working directory to backend
WORKDIR /app/backend

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app && \
    chown -R app:app /data

# Switch to non-root user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/health || exit 1

# Expose port (Railway will set PORT environment variable)
EXPOSE 8080

# Start command optimized for Railway
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--worker-class", "gevent", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "src.main:app"]

