import logging

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from models.document import DocumentChunk
from config.extensions.database_config import db
from config.document_services.embedding_services import (generate_query_embedding)


logger = logging.getLogger(__name__)

def search_documents(question: str, top_k: int = 5):
    logger.info(
        f"Starting document search. Question length: {len(question) if question else 0}")
    
    try:
        if not question or not question.strip():
            logger.warning("Empty question received for document search.")
            return []


        if top_k <= 0:
            logger.warning(f"Invalid top_k value: {top_k}")
            return []
        
        logger.info("Generating query embedding.")
        query_embedding = generate_query_embedding(question)

        if not query_embedding:
            logger.error("Generated query embedding is empty.")
            return []


        if len(query_embedding) != 384:
            logger.error(f"Invalid embedding dimension. Expected 384, got {len(query_embedding)}")
            raise ValueError("Invalid embedding dimension.")

        if not isinstance(query_embedding[0], float):
            logger.error("Embedding format invalid. Expected list of floats.")

            raise ValueError("Invalid embedding format.")


        logger.info("Query embedding generated successfully.")

        stmt = (
            select(
                DocumentChunk,
                DocumentChunk.embedding
                .cosine_distance(query_embedding)
                .label("distance")
            )
            .order_by("distance")
            .limit(top_k)
        )

        logger.info(f"Executing vector search. top_k={top_k}")
        results = db.session.execute(stmt).all()

        if not results:
            logger.info("No matching document chunks found.")
            return []

        logger.info(f"Document search completed. Found {len(results)} results.")
        return results


    except SQLAlchemyError as e:
        logger.exception(f"Database error during document search: {str(e)}")
        db.session.rollback()
        raise


    except ValueError as e:
        logger.exception(f"Embedding validation failed: {str(e)}")
        raise


    except Exception as e:
        logger.exception(f"Unexpected error during document search: {str(e)}")
        raise