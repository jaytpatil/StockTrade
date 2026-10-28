FROM python:3.8.0-slim

WORKDIR /app

# System dependencies for ML/Data science libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Entrypoint for celery worker
CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
