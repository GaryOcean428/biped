# Use Python 3.11 official image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Set environment variables
ENV PYTHONPATH=/app/backend/src
ENV FLASK_APP=main.py

# Expose port
EXPOSE 8080

# Create startup script
RUN echo '#!/bin/bash\ncd /app/backend && python -m gunicorn --bind 0.0.0.0:$PORT src.main:app' > /app/start.sh
RUN chmod +x /app/start.sh

# Start the application
CMD ["/app/start.sh"]

