FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (supporting both root and backend-relative build contexts)
COPY requirements.txt* backend/requirements.txt* ./
RUN if [ -f "requirements.txt" ]; then \
        pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt; \
    elif [ -f "backend/requirements.txt" ]; then \
        pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r backend/requirements.txt; \
    fi

# Copy application source
COPY . .

ENV PYTHONPATH=/app
ENV HOST=0.0.0.0
ENV PORT=8000
ENV ENVIRONMENT=production

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
