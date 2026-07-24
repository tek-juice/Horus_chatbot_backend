import logging
import os
from werkzeug.utils import secure_filename
from config.document_services.save_document import save_document


logger = logging.getLogger(__name__)

UPLOAD_FOLDER = "uploads/documents"

def ingest_document(file, admin_id):
    try:
        logger.info(
            f"Starting document ingestion: {file.filename}"
        )

        if not os.path.exists(UPLOAD_FOLDER):
            os.makedirs(UPLOAD_FOLDER)

            logger.info(
                f"Created upload directory: {UPLOAD_FOLDER}"
            )

        filename = secure_filename(file.filename)

        file_path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        file.save(file_path)

        logger.info(
            f"Document saved successfully: {file_path}"
        )

        # Save document metadata to the database
        document = save_document(
            filename=filename,
            file_path=file_path,
            file_type=file.content_type,
            created_by=admin_id
        )

        logger.info(
            f"Document record created with ID: {document.id}"
        )

        logger.info(
            f"Document ingestion completed successfully: {filename}"
        )

        return {
            "document_id": document.id,
            "filename": document.filename,
            "status": "completed",
            "message": "Document processed successfully."
        }

    except Exception as e:
        logger.exception(
            f"Document ingestion failed for '{file.filename if file else 'unknown'}': {e}"
        )
        raise