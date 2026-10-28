# Use active Python slim image
FROM python:3.9-slim

WORKDIR /app

# Set environment paths and system dependencies needed for XGBoost and psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Cache and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose backend REST port
EXPOSE 8000

# Run Uvicorn ASGI server bridging FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
