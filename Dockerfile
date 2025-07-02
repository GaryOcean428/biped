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
ENV PYTHONPATH=/app/backend
ENV FLASK_APP=src.main:app

# Expose port (Railway will set PORT environment variable)
EXPOSE $PORT

# Change to backend directory and start with gunicorn
WORKDIR /app/backend
CMD ["sh", "-c", "python -m gunicorn --bind 0.0.0.0:$PORT src.main:app"]

