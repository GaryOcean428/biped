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

# Set working directory to backend
WORKDIR /app/backend

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV FLASK_APP=src.main:app

# Expose port
EXPOSE 8080

# Run the application directly with Python
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "src.main:app"]

