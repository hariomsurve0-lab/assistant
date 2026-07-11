import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jarvis.log")

def setup_logger():
    logger = logging.getLogger("JARVIS")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if setup multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating File Handler
    try:
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=3, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"[Logger] Failed to create file handler: {e}")

    logger.info("Logger setup completed successfully.")
    return logger

logger = setup_logger()
