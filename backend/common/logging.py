"""
Structured JSON Logging Module

Provides production-ready logging with JSON formatting for easy parsing
by log aggregation tools (ELK, CloudWatch, etc.)
"""

import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any
from common.config import settings


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON.
    
    Includes standard fields: timestamp, level, message, module, function, line.
    Additional context can be passed via the 'extra' parameter.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request context if available
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "path"):
            log_obj["path"] = record.path
        if hasattr(record, "method"):
            log_obj["method"] = record.method
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        if hasattr(record, "duration_ms"):
            log_obj["duration_ms"] = record.duration_ms
        if hasattr(record, "event"):
            log_obj["event"] = record.event
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_obj, default=str)


class SimpleFormatter(logging.Formatter):
    """Simple colored formatter for development."""
    
    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Include extra context if available
        extra = ""
        if hasattr(record, "request_id"):
            extra += f" [req:{record.request_id[:8]}]"
        if hasattr(record, "user_id"):
            extra += f" [user:{record.user_id[:8]}]"
        
        return (
            f"{color}{timestamp} | {record.levelname:8}{self.RESET}"
            f"{extra} | {record.name}:{record.funcName}:{record.lineno}"
            f" - {record.getMessage()}"
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level from settings
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        # Use JSON formatter in production, simple formatter in dev
        if settings.ENV == "production" or not settings.DEBUG:
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(SimpleFormatter())
        
        logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


# Create application logger
app_logger = get_logger("stock_platform")
