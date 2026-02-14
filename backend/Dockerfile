# Backend Dockerfile
FROM python:3.11-slim

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-deu \
    tesseract-ocr-tur \
    tesseract-ocr-eng \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodu
COPY . .

# Port
EXPOSE 8001

# Başlat
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
