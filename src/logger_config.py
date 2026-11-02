import logging
import os
import sys


class DynamicStdoutHandler(logging.StreamHandler):
    """Write log messages to the current stdout stream."""

    def emit(self, record: logging.LogRecord) -> None:
        self.stream = sys.stdout
        super().emit(record)


def configure_logger(name: str = "coverage_gate") -> logging.Logger:
    """Configure and return a logger for Coverage Gate."""
    logger = logging.getLogger(name)
    logger.setLevel(
        getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    )
    logger.propagate = False

    if not logger.handlers:
        handler = DynamicStdoutHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)

    return logger
