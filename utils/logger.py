"""Logger utility using Python's built-in logging module."""

import logging
import os
from logging.handlers import RotatingFileHandler

try:
    import colorlog  # optional coloured console output
    _HAS_COLORLOG = True
except ImportError:
    _HAS_COLORLOG = False

_LOGGERS: dict = {}


def get_logger(name: str = "chatgpt-bot") -> logging.Logger:
    """
    Return a named logger.  The logger is configured once and cached; subsequent
    calls with the same *name* return the cached instance.
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    # Lazy import to avoid a circular dependency at module import time.
    from config import config  # noqa: PLC0415

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.LOG_LEVEL, logging.INFO))

    if not logger.handlers:
        # ------------------------------------------------------------------ #
        # Console handler                                                      #
        # ------------------------------------------------------------------ #
        if _HAS_COLORLOG:
            console_fmt = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            )
        else:
            console_fmt = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_fmt)
        logger.addHandler(console_handler)

        # ------------------------------------------------------------------ #
        # File handler                                                         #
        # ------------------------------------------------------------------ #
        log_dir = os.path.dirname(config.LOG_FILE)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler = RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=5,
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

    _LOGGERS[name] = logger
    return logger
