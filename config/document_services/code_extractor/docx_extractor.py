import logging
from docx import Document

logger = logging.getLogger(__name__)


def extract_docx(file_path):
    try:
        logger.info(
            f"Extracting text from DOCX: {file_path}"
        )

        document = Document(file_path)

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
        )

        logger.info(
            "DOCX text extraction completed."
        )

        return text.strip()

    except Exception as e:
        logger.exception(
            f"Failed to extract DOCX text: {e}"
        )
        raise