import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logging():
    if not os.path.exists("logs"):
        os.makedirs("logs")
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
    logging.getLogger().addHandler(file_handler)
    logging.getLogger().setLevel(logging.INFO)