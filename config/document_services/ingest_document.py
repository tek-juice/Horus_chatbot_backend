import logging
import os
from werkzeug.utils import secure_filename
from config.document_services.save_document import save_document
from config.document_services.document_loader import extract_text
from config.document_services.create_chunks import create_chunks
from config.document_services.embedding_services import generate_embeddings
from config.document_services.save_chunks import save_chunks

logger = logging.getLogger(__name__)

UPLOAD_FOLDER = "uploads/documents"


def ingest_document(file, admin_id):
    try:
        logger.info(f"Starting document ingestion: {file.filename}")

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)
            logger.info(f"Created upload directory: {UPLOAD_FOLDER}")

        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        file.save(file_path)
        logger.info(f"Document saved successfully: {file_path}")

        # Save document metadata
        document = save_document(
            filename=filename,
            file_path=file_path,
            file_type=file.content_type,
            created_by=admin_id
        )

        logger.info(f"Document record created with ID: {document.id}")

        # Extract text
        logger.info(f"Extracting text from document {document.id}.")
        text = extract_text(document.file_path)
        logger.info("Text extraction completed.")

        # Create chunks
        logger.info("Creating document chunks.")
        chunks = create_chunks(text=text)
        logger.info(f"{len(chunks)} chunks created.")

        # Generate embeddings
        logger.info("Generating embeddings.")
        embeddings = generate_embeddings(chunks)
        logger.info(f"{len(embeddings)} embeddings generated.")

        # Save chunks
        logger.info("Saving document chunks.")

        save_chunks(
            document_id=document.id,
            chunks=chunks,
            embeddings=embeddings
        )
        logger.info("Document chunks saved successfully.")
        logger.info(f"Document ingestion completed successfully: {filename}")

        return {
            "document_id": document.id,
            "filename": document.filename,
            "chunks_created": len(chunks),
            "status": "completed",
            "message": "Document processed successfully."
        }

    except Exception as e:
        logger.exception(
            f"Document ingestion failed for '{file.filename if file else 'unknown'}': {e}"
        )
        raise