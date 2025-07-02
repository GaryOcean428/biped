FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DATA_DIR=/data

# Create app directory
WORKDIR /app

# Create data directory and set permissions
RUN mkdir -p /data/uploads /data/logs /data/backups && \
    chmod -R 755 /data

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set working directory to backend
WORKDIR /app/backend

# Create entrypoint script
RUN echo '#!/bin/sh\n\
set -e\n\
\n\
# Ensure PORT is set (Railway provides this)\n\
if [ -z "$PORT" ]; then\n\
    echo "Warning: PORT not set, defaulting to 8080"\n\
    export PORT=8080\n\
fi\n\
\n\
echo "Starting Biped Platform on port: $PORT"\n\
echo "Current directory: $(pwd)"\n\
echo "Python version: $(python --version)"\n\
echo "Data directory: $DATA_DIR"\n\
\n\
# Ensure data directories exist\n\
mkdir -p /data/uploads /data/logs /data/backups\n\
chmod -R 755 /data\n\
\n\
# Execute the application\n\
exec python src/main.py' > /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Expose port
EXPOSE 8080

# Use entrypoint script
ENTRYPOINT ["/app/docker-entrypoint.sh"]

