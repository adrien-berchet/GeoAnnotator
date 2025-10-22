# Backend Dockerfile for GeoAnnotator
#
# Multi-stage build for production optimization

FROM python:3.11-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies including GDAL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# Create symbolic link for GDAL Python bindings from system to virtualenv
RUN GDAL_VERSION=$(gdal-config --version) && \
    echo "System GDAL version: $GDAL_VERSION" && \
    ln -s /usr/lib/python3/dist-packages/osgeo /usr/local/lib/python3.11/site-packages/osgeo

# Set GDAL environment variables
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so \
    GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so

# Set working directory
WORKDIR /app

# Install Python dependencies (GDAL is excluded, using system package)
COPY requirements/base.txt requirements/development.txt ./requirements/
RUN pip install --upgrade pip && \
    # Remove GDAL from base requirements
    grep -v "^GDAL" ./requirements/base.txt > /tmp/base-no-gdal.txt && \
    # Remove the -r base.txt line from development.txt and use our filtered base
    grep -v "^-r base.txt" ./requirements/development.txt > /tmp/dev-no-include.txt && \
    # Combine filtered base + filtered development
    cat /tmp/base-no-gdal.txt /tmp/dev-no-include.txt > /tmp/requirements.txt && \
    # Install all dependencies
    pip install -r /tmp/requirements.txt && \
    # Cleanup
    rm /tmp/base-no-gdal.txt /tmp/dev-no-include.txt /tmp/requirements.txt

# Copy application code
COPY . .

# Create media directory
RUN mkdir -p /app/media

# Expose port
EXPOSE 8000

# Development command (override in docker-compose.yml)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Production stage
FROM base AS production

# Install production dependencies only (excluding GDAL, using system package)
COPY requirements/production.txt ./requirements/
RUN grep -v "^-r base.txt" ./requirements/production.txt > /tmp/prod-no-include.txt && \
    pip install -r /tmp/prod-no-include.txt && \
    rm /tmp/prod-no-include.txt

# Collect static files
RUN python manage.py collectstatic --noinput

# Use gunicorn for production
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:10000", "--workers", "4"]
