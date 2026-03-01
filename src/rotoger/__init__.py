import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import orjson
import structlog
from whenever._whenever import Instant

# ---------------------------------------------------------------------------
# Constants / defaults
# ---------------------------------------------------------------------------
_DEFAULT_LOG_PATH = "."
_DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MiB
_DEFAULT_BACKUP_COUNT = 5

# Generic registry: add any stdlib logger name + its desired level here.
_DEFAULT_STDLIB_LOGGERS: dict[str, int] = {
    "root": logging.INFO,
    "uvicorn": logging.INFO,
    "sqlalchemy": logging.WARNING,
}

# Shared processor chain used by both structlog and the stdlib formatter.
_SHARED_PROCESSORS: list[structlog.types.Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="iso", utc=True),
    structlog.processors.format_exc_info,
]


def _build_handler(
    log_path: str,
    max_bytes: int,
    backup_count: int,
) -> RotatingFileHandler:
    log_dir = Path(log_path)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{Instant.now().py_datetime().strftime('%Y%m%d')}_{os.getpid()}.log"

    handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=_SHARED_PROCESSORS,
            processor=structlog.processors.JSONRenderer(
                serializer=lambda *a, **kw: orjson.dumps(*a, **kw).decode()
            ),
        )
    )
    return handler


def _configure_logger(
    log_path: str,
    max_bytes: int,
    backup_count: int,
    stdlib_loggers: dict[str, int],
) -> structlog.BoundLogger:
    """Configure structlog + stdlib loggers and return a bound logger."""
    structlog.configure(
        processors=[
            *_SHARED_PROCESSORS,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    handler = _build_handler(log_path, max_bytes, backup_count)

    for name, level in stdlib_loggers.items():
        logger = logging.getLogger(name)
        logger.addHandler(handler)
        logger.propagate = False
        logger.setLevel(level)

    return structlog.get_logger()


# Module-level singleton (populated on first get_logger() call)
_logger_instance: Optional[structlog.BoundLogger] = None


def get_logger(
    *,
    log_path: str = os.getenv("ROTOGER_LOG_PATH", _DEFAULT_LOG_PATH),
    max_bytes: int = int(os.getenv("ROTOGER_LOG_MAX_BYTES", _DEFAULT_MAX_BYTES)),
    backup_count: int = int(os.getenv("ROTOGER_LOG_BACKUP_COUNT", _DEFAULT_BACKUP_COUNT)),
    stdlib_loggers: Optional[dict[str, int]] = None,
) -> structlog.BoundLogger:
    """Return the configured singleton logger instance.

    On the **first** call the logger is initialised with the supplied kwargs
    (or their defaults / environment-variable overrides).  Subsequent calls
    return the already-configured singleton regardless of any kwargs passed.

    Args:
        log_path:       Directory where log files are written.
                        Env var: ``ROTOGER_LOG_PATH`` (default: ``"."``).
        max_bytes:      Maximum size of a single log file before rotation.
                        Env var: ``ROTOGER_LOG_MAX_BYTES`` (default: 10 MiB).
        backup_count:   Number of rotated log files to keep.
                        Env var: ``ROTOGER_LOG_BACKUP_COUNT`` (default: ``5``).
        stdlib_loggers: Mapping of stdlib logger name → log level.
                        Defaults to ``{"root": INFO, "uvicorn": INFO,
                        "sqlalchemy": WARNING}``.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = _configure_logger(
            log_path=log_path,
            max_bytes=max_bytes,
            backup_count=backup_count,
            stdlib_loggers=stdlib_loggers if stdlib_loggers is not None else _DEFAULT_STDLIB_LOGGERS,
        )
    return _logger_instance
