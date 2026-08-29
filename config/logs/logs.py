import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging():

    os.makedirs("logs", exist_ok=True)

    file_handler = RotatingFileHandler(
        "logs/app.log",
        maxBytes=10240,
        backupCount=10
    )

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    root_logger = logging.getLogger()

    root_logger.setLevel(logging.INFO)

    # Prevent duplicate handlers when Flask reloads
    if not root_logger.handlers:
        root_logger.addHandler(file_handler)