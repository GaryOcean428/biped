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

# Change to backend directory (best practice)
WORKDIR /app/backend

# Start the application using gunicorn (production-ready)
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:$PORT", "src.main:app"]

