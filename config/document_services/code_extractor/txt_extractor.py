import logging

logger = logging.getLogger(__name__)
def extract_txt(file_path):
    try:
        logger.info(
            f"Extracting text from TXT: {file_path}"
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as file:

            text = file.read()

        logger.info(
            "TXT extraction completed."
        )

        return text.strip()

    except Exception as e:
        logger.exception(
            f"Failed to extract TXT: {e}"
        )
        raise