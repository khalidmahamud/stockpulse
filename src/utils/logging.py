"""
Structured logging configuration for StockPulse.

Usage:
    from src.utils.logging import get_logger
    
    logger = get_logger(__name__)
    logger.info("something_happened", ticker="AAPL", rows=365)
"""

import sys
import logging
import structlog
from structlog.typing import Processor

from src.utils.config import get_settings


def setup_logging() -> None:
    """
    Configure structured logging for the application.
    
    Call this once at application startup.
    """
    settings = get_settings()
    log_level = settings["app"].log_level
    environment = settings["app"].environment
    
    # Determine if we're in development or production
    is_development = environment == "development"
    
    # Shared processors for all log entries
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]
    
    if is_development:
        # Pretty, colorful output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True)
        ]
    else:
        # JSON output for production (machine-parseable)
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer()
        ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Also configure standard library logging (for third-party libs)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(log_level),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance for a module.
    
    Args:
        name: Usually __name__ of the calling module.
        
    Returns:
        A structured logger instance.
        
    Example:
        logger = get_logger(__name__)
        logger.info("user_logged_in", user_id=123)
    """
    return structlog.get_logger(name)