FROM python:3.10-slim

RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/bash appuser

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-mar \
    poppler-utils \
    fonts-freefont-ttf \
    libgl1 \
    ghostscript \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir -p /home/appuser/.EasyOCR && \
    chown -R appuser:appgroup /home/appuser/.EasyOCR

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appgroup /app

USER appuser

CMD ["python", "app/ui.py"]
