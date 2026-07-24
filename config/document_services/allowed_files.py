import logging

logger = logging.getLogger(__name__)


ALLOWED_EXTENSIONS = {
    "pdf",
    "docx"
}


ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


def allowed_file(filename: str) -> bool:
    """
    Validate uploaded file extension.

    Args:
        filename (str): Uploaded filename.

    Returns:
        bool: True if extension is allowed.
    """

    try:
        if not filename:
            logger.warning("File validation failed: Empty filename.")
            return False

        extension = filename.rsplit(".", 1)[1].lower() if "." in filename else ""

        if extension not in ALLOWED_EXTENSIONS:
            logger.warning(
                f"File validation failed: Unsupported extension '{extension}'."
            )
            return False

        logger.info(
            f"File extension validation successful for '{filename}'."
        )

        return True

    except Exception as e:
        logger.exception(
            f"Unexpected error validating file extension: {e}"
        )
        return False



def allowed_mimetype(content_type: str) -> bool:
    """
    Validate uploaded file MIME type.

    Args:
        content_type (str): File MIME type.

    Returns:
        bool: True if MIME type is allowed.
    """

    try:
        if not content_type:
            logger.warning(
                "MIME validation failed: Missing content type."
            )
            return False

        if content_type not in ALLOWED_MIME_TYPES:
            logger.warning(
                f"MIME validation failed: Unsupported type '{content_type}'."
            )
            return False

        logger.info(
            f"MIME validation successful: {content_type}"
        )

        return True

    except Exception as e:
        logger.exception(
            f"Unexpected error validating MIME type: {e}"
        )
        return False