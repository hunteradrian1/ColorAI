# Multi-stage build for ColorAI ML Colorization App
FROM python:3.9-slim as python-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Python stage
FROM python-base as python-deps

# Copy requirements and install Python dependencies
COPY ml/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Node.js stage  
FROM python-base as node-deps

# Copy package files and install Node dependencies
COPY client/package*.json /app/client/
WORKDIR /app/client
RUN npm ci --only=production

# Final stage
FROM python-base as runtime

# Copy Python dependencies
COPY --from=python-deps /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy Node dependencies
COPY --from=node-deps /app/client/node_modules /app/client/node_modules

# Set working directory
WORKDIR /app

# Copy application code
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/output /app/ml/models

# Set environment variable for production
ENV REACT_APP_API_URL=/api

# Build React app
WORKDIR /app/client
RUN npm run build

# Set up Python path
ENV PYTHONPATH=/app/ml/code

# Expose ports
EXPOSE 4000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:4000/api || exit 1

# Start the Flask server
WORKDIR /app
CMD ["python3", "server/local_server.py"]
