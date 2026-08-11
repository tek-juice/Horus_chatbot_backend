import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from models.document import DocumentChunk
from config.extensions.database_config import db
from config.document_services.embedding_services import (
    generate_query_embedding
)

logger = logging.getLogger(__name__)


def search_documents(
    question: str,
    top_k: int = 5,
    similarity_threshold: float = 0.6
):
    logger.info(
        f"Starting document search. "
        f"Question length: {len(question) if question else 0}, "
        f"top_k={top_k}, "
        f"similarity_threshold={similarity_threshold}"
    )

    try:
        if not question or not question.strip():
            logger.warning(
                "Empty question received for document search."
            )
            return []

        if top_k <= 0:
            logger.warning(
                f"Invalid top_k value: {top_k}"
            )
            return []

        if not 0.0 <= similarity_threshold <= 1.0:
            logger.warning(
                f"Invalid similarity threshold: "
                f"{similarity_threshold}"
            )
            raise ValueError(
                "similarity_threshold must be between 0.0 and 1.0."
            )

        # Convert similarity threshold to cosine distance
        distance_threshold = 1.0 - similarity_threshold

        logger.info(
            f"Using cosine distance threshold: "
            f"{distance_threshold}"
        )

        logger.info("Generating query embedding.")

        query_embedding = generate_query_embedding(question)

        if not query_embedding:
            logger.error(
                "Generated query embedding is empty."
            )
            return []

        if len(query_embedding) != 384:
            logger.error(
                f"Invalid embedding dimension. "
                f"Expected 384, got {len(query_embedding)}"
            )
            raise ValueError(
                "Invalid embedding dimension."
            )

        if not all(
            isinstance(value, float)
            for value in query_embedding
        ):
            logger.error(
                "Embedding format invalid. "
                "Expected list of floats."
            )
            raise ValueError(
                "Invalid embedding format."
            )

        logger.info(
            "Query embedding generated successfully."
        )

        distance = (
            DocumentChunk.embedding
            .cosine_distance(query_embedding)
        )

        stmt = (
            select(
                DocumentChunk,
                distance.label("distance")
            )
            .where(
                distance <= distance_threshold
            )
            .order_by(distance)
            .limit(top_k)
        )

        logger.info(
            f"Executing vector search. "
            f"top_k={top_k}, "
            f"distance_threshold={distance_threshold}"
        )

        results = db.session.execute(stmt).all()

        if not results:
            logger.info(
                "No document chunks passed the similarity threshold."
            )
            return []

        logger.info(
            f"Document search completed. "
            f"Found {len(results)} relevant results."
        )

        for index, (document, distance_value) in enumerate(results):
            similarity = 1.0 - float(distance_value)

            logger.info(
                f"Result {index + 1}: "
                f"similarity={similarity:.4f}, "
                f"distance={float(distance_value):.4f}"
            )

        return results

    except SQLAlchemyError as e:
        logger.exception(
            f"Database error during document search: {str(e)}"
        )
        db.session.rollback()
        raise

    except ValueError as e:
        logger.exception(
            f"Embedding validation failed: {str(e)}"
        )
        raise

    except Exception as e:
        logger.exception(
            f"Unexpected error during document search: {str(e)}"
        )
        raise