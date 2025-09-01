"""
Structured logging configuration
"""
import logging
import structlog
import sys
from typing import Any
from pythonjsonlogger import jsonlogger

from app.config import settings


def setup_logging():
    """Setup structured logging with JSON format"""
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper())
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add log level
            structlog.stdlib.add_log_level,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="ISO"),
            # Add caller information in debug mode
            structlog.dev.set_exc_info if settings.debug else lambda _, __, evt_dict: evt_dict,
            # Convert to JSON
            structlog.processors.JSONRenderer() if not settings.debug else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure JSON formatter for non-structlog loggers
    if not settings.debug:
        json_formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        
        # Apply JSON formatter to root logger
        for handler in root_logger.handlers:
            handler.setFormatter(json_formatter)
    
    # Get logger for this module
    logger = structlog.get_logger(__name__)
    logger.info("logging_configured", debug_mode=settings.debug, log_level=settings.log_level)