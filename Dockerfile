FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    gcc \
    libpq-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "server.shadow_service:app", "--bind", "0.0.0.0:10000", "--workers", "4", "--threads", "2", "--timeout", "120"]
