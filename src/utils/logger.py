"""
Logging configuration for DDA toolkit
"""

import logging
import logging.handlers
from pathlib import Path
import yaml


def setup_logger(name: str = 'dda', config_file: str = None) -> logging.Logger:
    """
    Set up logger with file and console handlers.

    Args:
        name: Logger name
        config_file: Path to config file

    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)

    # Default configuration
    log_level = logging.INFO
    log_file = 'logs/dda.log'
    max_bytes = 10 * 1024 * 1024  # 10 MB
    backup_count = 5
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Load from config if provided
    if config_file and Path(config_file).exists():
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
                logging_config = config.get('logging', {})

                log_level = getattr(logging, logging_config.get('level', 'INFO'))
                log_file = logging_config.get('file', log_file)
                max_bytes = logging_config.get('max_size_mb', 10) * 1024 * 1024
                backup_count = logging_config.get('backup_count', 5)
                log_format = logging_config.get('format', log_format)
        except Exception as e:
            print(f"Warning: Could not load logging config: {e}")

    # Set log level
    logger.setLevel(log_level)

    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(log_format))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
