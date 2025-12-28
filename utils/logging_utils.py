import logging
from typing import Optional


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create or retrieve a configured logger with a concise format.

    This avoids duplicate handlers and keeps logs consistent across CLI and UI.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
    return logger


def set_global_log_level(level: int) -> None:
    """Set global logging level for root and existing loggers."""
    logging.getLogger().setLevel(level)
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).setLevel(level)
