FROM python:3.10-slim

WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt /app/backend/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy backend code
COPY backend/ /app/backend/

# Copy .env if exists
COPY .env* /app/

EXPOSE 5000

# Use shell form so $PORT expands on Render
CMD ["sh", "-c", "gunicorn backend.app:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 30"]
