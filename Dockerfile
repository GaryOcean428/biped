# Use Python 3.11 official image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . /app/

# Change to backend directory
WORKDIR /app/backend

# Expose port (Railway will set PORT environment variable)
EXPOSE 8080

# Create a startup script to handle PORT environment variable
RUN echo '#!/bin/bash\nPORT=${PORT:-8080}\nexec gunicorn --bind 0.0.0.0:$PORT src.main:app' > /app/start.sh
RUN chmod +x /app/start.sh

# Command to run the application
CMD ["/app/start.sh"]

