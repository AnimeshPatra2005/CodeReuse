"""
Logging utility using loguru for structured logging.
"""

import sys
from pathlib import Path
from loguru import logger
from typing import Optional


class Logger:
    """Centralized logger for the application."""
    
    _initialized = False
    
    @classmethod
    def setup(
        cls,
        level: str = "INFO",
        log_file: Optional[str] = None,
        rotation: str = "10 MB",
        retention: str = "1 week",
        format_string: Optional[str] = None
    ):
        """
        Setup the logger with specified configuration.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file (optional)
            rotation: When to rotate log file
            retention: How long to keep old logs
            format_string: Custom format string
        """
        if cls._initialized:
            return
        
        # Remove default handler
        logger.remove()
        
        # Default format
        if format_string is None:
            format_string = (
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            )
        
        # Add console handler
        logger.add(
            sys.stderr,
            format=format_string,
            level=level,
            colorize=True
        )
        
        # Add file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.add(
                log_file,
                format=format_string,
                level=level,
                rotation=rotation,
                retention=retention,
                compression="zip"
            )
        
        cls._initialized = True
        logger.info(f"Logger initialized with level: {level}")
    
    @classmethod
    def get_logger(cls, name: str = __name__):
        """
        Get a logger instance.
        
        Args:
            name: Name for the logger (usually __name__)
            
        Returns:
            Logger instance
        """
        if not cls._initialized:
            cls.setup()
        
        return logger.bind(name=name)


# Convenience function
def get_logger(name: str = __name__):
    """Get a logger instance."""
    return Logger.get_logger(name)

# Made with Bob
