FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
        gcc \
        libpq-dev \
        espeak-ng && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install \
    --default-timeout=600 \
    --retries=10 \
    --no-cache-dir \
    torch \
    --index-url https://download.pytorch.org/whl/cpu

RUN pip install \
    --default-timeout=600 \
    --retries=10 \
    --no-cache-dir \
    -r requirements.txt


# 1. FastEmbed - BAAI/bge-small-en-v1.5
RUN python -c "\
from fastembed import TextEmbedding; \
print('Downloading FastEmbed model...'); \
TextEmbedding(model_name='BAAI/bge-small-en-v1.5'); \
print('FastEmbed model ready.')"

# 2. Faster-Whisper - small
RUN python -c "\
from faster_whisper import WhisperModel; \
print('Downloading Faster-Whisper small model...'); \
WhisperModel('small', device='cpu', compute_type='int8'); \
print('Faster-Whisper model ready.')"

# 3. Kokoro - Kokoro-82M + required assets/voice
RUN python -c "\
from kokoro import KPipeline; \
print('Downloading Kokoro model and assets...'); \
pipeline = KPipeline(lang_code='a'); \
print('Downloading af_heart voice...'); \
pipeline.load_voice('af_heart'); \
print('Kokoro model and af_heart voice ready.')"

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]