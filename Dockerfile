FROM python:3.11-slim

WORKDIR /app

# Create data directory for SQLite
RUN mkdir -p /data

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ app/

# Set environment defaults
ENV HEALTH_TRACKER_DATABASE_PATH=/data/health.db
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run the application - use shell form to expand $PORT
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level info
