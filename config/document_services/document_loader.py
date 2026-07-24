import logging
import os
from config.document_services.code_extractor.docx_extractor import extract_docx
from config.document_services.code_extractor.pdf_extractor import extract_pdf
from config.document_services.code_extractor.txt_extractor import extract_txt

logger = logging.getLogger(__name__)

def extract_text(file_path):
    extension = os.path.splitext(file_path)[1].lower()

    if extension == ".pdf":
        return extract_pdf(file_path)

    elif extension == ".docx":
        return extract_docx(file_path)

    elif extension == ".txt":
        return extract_txt(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )