FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Add the app directory to PYTHONPATH
ENV PYTHONPATH=/app

# Make sure scripts are executable
RUN chmod +x /app/entrypoint.sh

# Create an entrypoint script
COPY entrypoint.sh /app/entrypoint.sh