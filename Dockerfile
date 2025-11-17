# Production Dockerfile for Kain Saan
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Create a non-root user for security
RUN useradd -m -u 1000 kainsaan && chown -R kainsaan:kainsaan /app
USER kainsaan

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/', timeout=5)"

# Run gunicorn - Use PORT env var for Railway compatibility
CMD gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 2 --threads 4 --worker-class gthread --access-logfile - --error-logfile - kainsaan.wsgi:application
