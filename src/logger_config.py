import logging
import os


def configure_logger(name: str = "coverage_gate") -> logging.Logger:
    """Configure and return a logger for Coverage Gate."""
    logger = logging.getLogger(name)
    logger.setLevel(
        getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    )
    logger.propagate = False

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)

    return logger
