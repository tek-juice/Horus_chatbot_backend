import logging

from config.extensions.database_config import db
from models.document import DocumentChunk

logger = logging.getLogger(__name__)


def save_chunks(document_id: int, chunks: list[str], embeddings: list[list[float]]):

    try:
        if len(chunks) != len(embeddings):
            raise ValueError(
                "Number of chunks must match number of embeddings."
            )

        logger.info(
            f"Saving {len(chunks)} chunks for document {document_id}."
        )

        document_chunks = []

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings),
            start=1
        ):

            document_chunk = DocumentChunk(
                document_id=document_id,
                chunk_number=index,
                content=chunk,
                embedding=embedding
            )

            db.session.add(document_chunk)

            document_chunks.append(document_chunk)

        db.session.commit()

        logger.info(
            f"Successfully saved {len(document_chunks)} chunks for document {document_id}."
        )

        return document_chunks

    except Exception as e:

        db.session.rollback()

        logger.exception(
            f"Failed to save chunks for document {document_id}: {e}"
        )

        raise