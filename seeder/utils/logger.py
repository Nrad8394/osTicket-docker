"""
utils/logger.py - Logging configuration and utilities

Provides centralized logging setup for seeding operations.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

# Get the seeder directory
SEEDER_DIR = Path(__file__).parent.parent
LOGS_DIR = SEEDER_DIR / 'logs'

# Create logs directory if it doesn't exist
LOGS_DIR.mkdir(exist_ok=True)


class LoggerSetup:
    """Configure and manage loggers."""
    
    _configured = False
    
    @classmethod
    def configure(cls, name: str = 'osticket_seeder',
                 log_file: Optional[str] = None,
                 level: int = logging.INFO) -> logging.Logger:
        """Configure logger.
        
        Args:
            name: Logger name
            log_file: Log file name (in logs directory)
            level: Logging level
        
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        
        # Avoid duplicate handlers
        if cls._configured and logger.handlers:
            return logger
        
        logger.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler
        if log_file is None:
            log_file = f'{name}.log'
        
        log_path = LOGS_DIR / log_file
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        cls._configured = True
        return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
