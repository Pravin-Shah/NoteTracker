"""
Centralized logging configuration.
"""

import logging
from logging.handlers import RotatingFileHandler
from core.config import LOG_LEVEL, LOG_FILE


def setup_logger():
    """Setup logging for all modules."""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL))

    # File handler
    fh = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5_000_000,  # 5MB
        backupCount=5
    )
    fh.setLevel(getattr(logging, LOG_LEVEL))

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(getattr(logging, LOG_LEVEL))

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger
