"""Unified logging configuration for the application."""

import logging
import os
from pathlib import Path


def setup_logging(log_level: int = logging.INFO, log_file: str = None) -> None:
    """Set up logging configuration for the entire application.

    Parameters
    ----------
    log_level : int, optional
        The logging level to use, defaults to logging.INFO
    log_file : str, optional
        Path to the log file, defaults to 'logs/app.log'
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Default log file if not specified
    if log_file is None:
        log_file = log_dir / "app.log"

    # Configure logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(log_format, date_format)

    # Set up file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Set up console handler with color formatting if available
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicates when re-configuring
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info("Logging initialized: level=%s, file=%s", logging.getLevelName(log_level), log_file)

    # Log environment info for debugging
    logger.debug("Python environment: %s", os.environ.get("VIRTUAL_ENV", "system"))
