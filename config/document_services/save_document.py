import logging
from models.document import Document
from config.extensions.database_config import db

logger = logging.getLogger(__name__)


def save_document(
    filename,
    file_path,
    file_type,
    created_by
):

    try:
        document = Document(
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            created_by=created_by
        )

        db.session.add(document)
        db.session.commit()

        logger.info(
            f"Document saved: {document.id}"
        )

        return document

    except Exception as e:

        db.session.rollback()

        logger.exception(
            f"Failed saving document: {e}"
        )

        raise