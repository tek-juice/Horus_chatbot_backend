from flask import Blueprint, jsonify, request
from config.helpers.helpers import admin_required
from config.document_services.allowed_files import allowed_file, allowed_mimetype
from config.document_services.ingest_document import ingest_document
from flasgger import swag_from
import logging
from flask_jwt_extended import get_jwt_identity

logger = logging.getLogger(__name__)

document = Blueprint("document", __name__, url_prefix="/document")
@document.post("/ingest")
@admin_required
@swag_from({
    "tags": ["Document"],
    "summary": "Upload and ingest document",
    "description": "Uploads a PDF or DOCX document, extracts its text, chunks it, generates embeddings using BAAI/bge-small-en-v1.5, and stores the embeddings for semantic search.",
    "consumes": [
        "multipart/form-data"
    ],
    "security": [
        {
            "Bearer": []
        }
    ],
    "parameters": [
        {
            "name": "file",
            "in": "formData",
            "type": "file",
            "required": True,
            "description": "PDF or DOCX document to ingest."
        }
    ],
    "responses": {
        "201": {
            "description": "Document ingested successfully."
        },
        "400": {
            "description": "Invalid file or request."
        },
        "401": {
            "description": "Unauthorized."
        },
        "403": {
            "description": "Forbidden."
        },
        "500": {
            "description": "Internal server error."
        }
    }
})
def upload_document():
    admin_id = get_jwt_identity()
    try:
        logger.info("Document upload request received.")

        if "file" not in request.files:
            logger.warning("Upload failed: No file provided in request.")

            return jsonify({
                "success": False,
                "message": "No file uploaded."
            }), 400

        file = request.files["file"]

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "message": "Only PDF and DOCX files are allowed."
            }), 400

        if not allowed_mimetype(file.content_type):
            return jsonify({
                "success": False,
                "message": "Invalid document format."
            }), 400

        result = ingest_document(file, admin_id)

        logger.info(
            f"Document '{file.filename}' ingested successfully."
        )

        return jsonify({
            "success": True,
            "message": "Document ingested successfully.",
            "data": result
        }), 201

    except Exception as e:
        logger.exception(
            f"Unexpected error while ingesting document '{request.files.get('file').filename if request.files.get('file') else 'Unknown'}': {e}"
        )

        return jsonify({
            "success": False,
            "error": str(e),
            # "message": "An unexpected error occurred while ingesting the document."
        }), 500