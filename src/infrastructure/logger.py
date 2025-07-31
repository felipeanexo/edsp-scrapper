"""
Structured logging infrastructure with context binding.
"""

import sys
from typing import Dict, Any
from contextvars import ContextVar
from loguru import logger
from datetime import datetime


class StructuredLogger:
    """Structured logger with context binding capabilities."""

    def __init__(self):
        self._context: ContextVar[Dict[str, Any]] = ContextVar("context", default={})
        self._setup_logger()

    def _setup_logger(self):
        """Configure logger with structured format."""
        logger.remove()

        # Console output with structured format
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}",
            level="INFO",
            colorize=True,
        )

        # File output with JSON-like structure
        logger.add(
            "logs/edsp_scraper_{time}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {extra[context]} | {message}",
            level="DEBUG",
            rotation="1 day",
            retention="7 days",
            compression="zip",
        )

    def bind_context(self, **kwargs):
        """Bind context variables to the logger."""
        current_context = self._context.get()
        current_context.update(kwargs)
        self._context.set(current_context)
        return logger.bind(context=str(current_context))

    def log_processing_start(self, batch_name: str, start_page: int, end_page: int):
        """Log processing start with context."""
        self.bind_context(
            batch=batch_name,
            start_page=start_page,
            end_page=end_page,
            timestamp=datetime.now().isoformat(),
        ).info("🚀 Starting batch processing")

    def log_page_processing(self, page_num: int, schools_found: int):
        """Log page processing with context."""
        self.bind_context(page=page_num, schools_found=schools_found).info(
            f"📄 Processing page {page_num}: {schools_found} schools found"
        )

    def log_school_processing(self, school_name: str, detail_url: str, status: str):
        """Log school processing with context."""
        self.bind_context(
            school_name=school_name, detail_url=detail_url, status=status
        ).info(f"🏫 Processing school: {school_name}")

    def log_error(self, error: Exception, context: str = ""):
        """Log error with context."""
        self.bind_context(
            error_type=type(error).__name__, error_message=str(error), context=context
        ).error(f"❌ Error occurred: {error}")

    def log_stats(self, stats: Dict[str, Any]):
        """Log statistics with context."""
        self.bind_context(**stats).info("📊 Processing statistics")

    def log_completion(self, total_schools: int, success_rate: float):
        """Log completion with context."""
        self.bind_context(total_schools=total_schools, success_rate=success_rate).info(
            f"✅ Processing completed: {total_schools} schools, {success_rate:.1f}% success rate"
        )


# Global logger instance
structured_logger = StructuredLogger()
