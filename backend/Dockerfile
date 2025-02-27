FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set proper permissions for entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Add the app directory to PYTHONPATH
ENV PYTHONPATH=/app

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]