"""Logging configuration for Numen."""

import sys
from loguru import logger


def setup_logger(level: str = "INFO"):
    """Configure logger."""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=level,
    )
    return logger
