# Använd en Python-bild som bas
FROM python:3.9-slim

# Sätt arbetskatalogen i containern
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopiera alla projektfiler till containern
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make the entrypoint script executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Exponera porten för FastAPI
EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
