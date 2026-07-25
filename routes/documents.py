from flask import Blueprint, jsonify, request, send_file
from config.helpers.helpers import admin_or_super_admin_required
from config.document_services.allowed_files import allowed_file, allowed_mimetype
from config.document_services.ingest_document import ingest_document
from flasgger import swag_from
import logging
from flask_jwt_extended import get_jwt_identity
from models.document import Document, DocumentChunk
import mimetypes
import os
from config.extensions.database_config import db


UPLOAD_FOLDER = os.path.abspath("uploads/documents")

logger = logging.getLogger(__name__)

document = Blueprint("document", __name__, url_prefix="/document")
@document.post("/ingest")
@admin_or_super_admin_required
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

@document.get("/view-list-documents")
@admin_or_super_admin_required
@swag_from({
    "tags": ["Document"],
    "summary": "Get all documents",
    "description": "Fetches metadata for all uploaded documents, ordered by newest first.",
    "security": [
        {
            "Bearer": []
        }
    ],
    "responses": {
        "200": {
            "description": "Documents fetched successfully.",
            "schema": {
                "type": "object",
                "properties": {
                    "success": {
                        "type": "boolean",
                        "example": True
                    },
                    "count": {
                        "type": "integer",
                        "example": 1
                    },
                    "documents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer",
                                    "example": 1
                                },
                                "filename": {
                                    "type": "string",
                                    "example": "About_Horus.pdf"
                                },
                                "file_type": {
                                    "type": "string",
                                    "example": "pdf"
                                },
                                "created_by": {
                                    "type": "integer",
                                    "example": 1
                                },
                                "created_at": {
                                    "type": "string",
                                    "format": "date-time",
                                    "example": "2026-07-25T10:30:00"
                                }
                            }
                        }
                    }
                }
            }
        },
        "401": {
            "description": "Unauthorized."
        },
        "403": {
            "description": "Forbidden."
        },
        "500": {
            "description": "Unable to fetch documents."
        }
    }
})
def get_documents():
    logger.info("Fetching document metadata.")
    try:
        documents = (Document.query.order_by(Document.created_at.desc()).all())
        if not documents:
            logger.info("No documents found.")
            return jsonify({
                "success": True,
                "count": 0,
                "documents": []
            }), 200

        document_list = []
        for document in documents:
            document_list.append({
                "id": document.id,
                "filename": document.filename,
                "file_type": document.file_type,
                "created_by": document.created_by,
                "created_at": document.created_at.isoformat()
            })

        logger.info(f"Retrieved {len(document_list)} documents.")

        return jsonify({
            "success": True,
            "count": len(document_list),
            "documents": document_list
        }), 200
    except Exception as e:
        logger.exception(
            f"Failed to fetch documents: {str(e)}"
        )

        return jsonify({
            "success": False,
            "error": "Unable to fetch documents."
        }), 500

@document.get("/view-document/<int:document_id>")
@admin_or_super_admin_required
@swag_from({
    "tags": ["Document"],
    "summary": "View or download a document",
    "description": (
        "Returns a document for preview. "
        "To force download, use ?download=true."
    ),
    "security": [
        {
            "Bearer": []
        }
    ],
    "parameters": [
        {
            "name": "document_id",
            "in": "path",
            "required": True,
            "type": "integer",
            "description": "Document ID"
        },
        {
            "name": "download",
            "in": "query",
            "required": False,
            "type": "boolean",
            "description": "Set to true to download the document."
        }
    ],
    "responses": {
        "200": {
            "description": "Document returned successfully."
        },
        "400": {
            "description": "Invalid document ID."
        },
        "403": {
            "description": "Access denied."
        },
        "404": {
            "description": "Document not found."
        },
        "500": {
            "description": "Server error."
        }
    }
})
def view_document(document_id):
    logger.info(f"Document request received. ID={document_id}")
    try:
        if document_id <= 0:
            logger.warning(
                f"Invalid document ID: {document_id}"
            )
            return jsonify({
                "success": False,
                "error": "Invalid document ID."
            }), 400

        document_record = Document.query.get(document_id)

        if not document_record:

            logger.warning(
                f"Document {document_id} not found."
            )

            return jsonify({
                "success": False,
                "error": "Document not found."
            }), 404

        if not document_record.file_path:
            logger.error(f"Document {document_id} has no file path.")

            return jsonify({
                "success": False,
                "error": "Document path is missing."
            }), 500

        file_path = os.path.abspath(document_record.file_path)

        if not file_path.startswith(UPLOAD_FOLDER):
            logger.error(f"Document {document_id} attempted access outside upload folder.")

            return jsonify({
                "success": False,
                "error": "Invalid document location."
            }), 403

        if not os.path.exists(file_path):

            logger.error(
                f"Document file missing: {file_path}"
            )

            return jsonify({
                "success": False,
                "error": "Document file not found."
            }), 404

        if not os.path.isfile(file_path):

            logger.error(
                f"Invalid file path: {file_path}"
            )

            return jsonify({
                "success": False,
                "error": "Invalid document."
            }), 500

        download = (
            request.args.get("download", "false")
            .strip()
            .lower() == "true"
        )

        logger.info(
            f"{'Downloading' if download else 'Previewing'} "
            f"document '{document_record.filename}'"
        )

        mime_type, _ = mimetypes.guess_type(file_path)

        if mime_type is None:
            mime_type = "application/octet-stream"

        return send_file(
            path_or_file=file_path,
            mimetype=mime_type,
            as_attachment=download,
            download_name=document_record.filename
        )

    except PermissionError:
        logger.exception(f"Permission denied reading document {document_id}")

        return jsonify({
            "success": False,
            "error": "Permission denied while accessing document."
        }), 500

    except FileNotFoundError:
        logger.exception(f"Document disappeared during request: {document_id}")
        return jsonify({
            "success": False,
            "error": "Document file not found."
        }), 404

    except OSError as e:
        logger.exception(f"OS error reading document {document_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Unable to access document."
        }), 500

    except Exception as e:
        logger.exception(f"Unexpected error viewing document {document_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred."
        }), 500


@document.delete("/delete-document/<int:document_id>")
@admin_or_super_admin_required
@swag_from({
    "tags": ["Document"],
    "summary": "Delete a document",
    "description": (
        "Deletes the document file, its metadata, and all associated "
        "document chunks (including embeddings)."
    ),
    "security": [
        {
            "Bearer": []
        }
    ],
    "parameters": [
        {
            "name": "document_id",
            "in": "path",
            "required": True,
            "type": "integer",
            "description": "Document ID"
        }
    ],
    "responses": {
        "200": {
            "description": "Document deleted successfully."
        },
        "400": {
            "description": "Invalid document ID."
        },
        "404": {
            "description": "Document not found."
        },
        "500": {
            "description": "Server error."
        }
    }
})
def delete_document(document_id):
    logger.info(f"Delete document request received. ID={document_id}")

    try:
        if document_id <= 0:
            logger.warning(f"Invalid document ID: {document_id}")
            return jsonify({
                "success": False,
                "error": "Invalid document ID."
            }), 400
        
        document_record = Document.query.get(document_id)
        if document_record is None:
            logger.warning(
                f"Document {document_id} not found."
            )

            return jsonify({
                "success": False,
                "error": "Document not found."
            }), 404

        logger.info(f"Document found: {document_record.filename}")

        chunks = DocumentChunk.query.filter_by(
            document_id=document_id
        ).all()

        logger.info(
            f"Found {len(chunks)} chunk(s) associated with document {document_id}."
        )

        if document_record.file_path:
            file_path = os.path.abspath(document_record.file_path)
            if not file_path.startswith(UPLOAD_FOLDER):
                logger.error(f"Document {document_id} points outside upload directory.")
                return jsonify({
                    "success": False,
                    "error": "Invalid document location."
                }), 403

            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"Deleted file: {file_path}")

                else:
                    logger.error(f"Expected file but found directory: {file_path}")
                    return jsonify({
                        "success": False,
                        "error": "Invalid document path."
                    }), 500

            else:
                logger.warning(
                    f"Physical file already missing: {file_path}"
                )

        deleted_chunks = (
            DocumentChunk.query
            .filter_by(document_id=document_id)
            .delete(synchronize_session=False)
        )

        logger.info(f"Deleted {deleted_chunks} document chunk(s).")
        db.session.delete(document_record)
        db.session.commit()
        logger.info(f"Document {document_id} deleted successfully.")
        return jsonify({
            "success": True,
            "message": "Document deleted successfully.",
            "deleted_chunks": deleted_chunks
        }), 200

    except PermissionError:
        db.session.rollback()
        logger.exception(f"Permission denied deleting document {document_id}.")
        return jsonify({
            "success": False,
            "error": "Permission denied while deleting document."
        }), 500

    except OSError as e:
        db.session.rollback()
        logger.exception(f"OS error deleting document {document_id}: {str(e)}")

        return jsonify({
            "success": False,
            "error": "Unable to delete document file."
        }), 500

    except Exception as e:
        db.session.rollback()
        logger.exception(f"Unexpected error deleting document {document_id}: {str(e)}")

        return jsonify({
            "success": False,
            "error": "An unexpected error occurred."
        }), 500