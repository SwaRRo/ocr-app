FROM python:3.10-slim

# 1. Create a non-root system user and group (UID/GID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -m -s /bin/bash appuser

# 2. Install system dependencies for OpenCV, Tesseract, Poppler, and FreeSans
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-mar \
    poppler-utils \
    fonts-freefont-ttf \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Set the working directory
WORKDIR /app

# 4. Pre-create the EasyOCR cache directory in the appuser's home directory
# and assign ownership so the unprivileged user can write to it without permission errors
RUN mkdir -p /home/appuser/.EasyOCR && \
    chown -R appuser:appgroup /home/appuser/.EasyOCR

# 5. Copy requirements and install as root first
# This ensures PyTorch and libraries are installed in global Python paths
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy the rest of the application files
COPY . .

# 7. Change ownership of the /app directory to our unprivileged user
RUN chown -R appuser:appgroup /app

# 8. Switch to the non-root user for all subsequent operations
USER appuser

# Set the default command to launch the Flask web UI
CMD ["python", "app/ui.py"]
