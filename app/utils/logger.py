import logging
from app.config import Config


def setup_logger(name: str) -> logging.Logger:
    """Setup logger with consistent formatting"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(getattr(logging, Config.LOG_LEVEL))

        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, Config.LOG_LEVEL))

        formatter = logging.Formatter(Config.LOG_FORMAT)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger