# logging.py
## 1. Introduction

# The `logging.py` file provides utilities for setting up logging in your application. It simplifies the process of configuring both file and console logging based on a provided configuration object.

# **Purpose:**
# - Configure root logger with specified settings.
# - Set log levels for different modules to control verbosity.
# - Format logs consistently for better readability.
import logging
from pathlib import Path
from config import AppConfig


def setup_logging(config: AppConfig):
    logger = logging.getLogger()  # Get the root logger
    logger.setLevel(config.logging.level.upper())  # Set global log level

    # Remove existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(config.paths.log_dir / "media_workflow.log")
    file_handler.setLevel(config.logging.level.upper())  # File handler level

    # Create stream handler (prints to screen)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(config.logging.level.upper())  # Stream handler level

    # Formatter
    formatter = logging.Formatter("[%(asctime)s][%(name)s][%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Optional: log an initial message
    logger.info("Logging setup complete.")

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("ppocr").setLevel(logging.WARNING)
