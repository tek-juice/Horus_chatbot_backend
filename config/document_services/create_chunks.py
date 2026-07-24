import logging

logger = logging.getLogger(__name__)


def create_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 100):
    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - chunk_overlap

    logger.info(
        f"Created {len(chunks)} chunks."
    )

    return chunks