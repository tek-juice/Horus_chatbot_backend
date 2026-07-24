import logging
import fitz 

logger = logging.getLogger(__name__)


def extract_pdf(file_path):

    try:
        logger.info(
            f"Extracting text from PDF: {file_path}"
        )

        document = fitz.open(file_path)

        text = ""

        for page in document:
            text += page.get_text()

        document.close()

        logger.info(
            "PDF text extraction completed."
        )

        return text.strip()

    except Exception as e:
        logger.exception(
            f"Failed to extract PDF text: {e}"
        )
        raise