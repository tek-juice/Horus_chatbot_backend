FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
        gcc \
        libpq-dev \
        espeak-ng && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch first
RUN pip install \
    --default-timeout=600 \
    --retries=10 \
    --no-cache-dir \
    torch \
    --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the dependencies
RUN pip install \
    --default-timeout=600 \
    --retries=10 \
    --no-cache-dir \
    -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]