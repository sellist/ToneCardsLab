import logging
import logging.config
import sys
from pathlib import Path
from typing import Dict, Any

from tcl_api.config.config import settings


class ColoredFormatter(logging.Formatter):

    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m'  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def get_logging_config() -> Dict[str, Any]:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": ColoredFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "()": ColoredFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "function": "%(funcName)s", "line": %(lineno)d, "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": "logs/tcl-api.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "encoding": "utf8"
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/tcl-api-errors.log",
                "maxBytes": 10485760,
                "backupCount": 5,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "tcl_api": {
                "level": "DEBUG" if settings.debug else "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file"]
        }
    }

    if settings.debug:
        config["handlers"]["console"]["level"] = "DEBUG"
        config["loggers"]["tcl_api"]["level"] = "DEBUG"
        config["root"]["level"] = "DEBUG"

    return config


def setup_logging() -> None:
    config = get_logging_config()
    logging.config.dictConfig(config)

    logger = logging.getLogger("tcl_api")
    logger.info("Logging system initialized")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {'DEBUG' if settings.debug else 'INFO'}")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(f"tcl_api.{name}")


app_logger = logging.getLogger("tcl_api")


def log_exception(logger: logging.Logger, exc: Exception, message: str = "An error occurred") -> None:
    logger.error(f"{message}: {str(exc)}", exc_info=True)


def log_request_error(logger: logging.Logger, request_info: str, exc: Exception) -> None:
    logger.error(f"Error processing request {request_info}: {str(exc)}", exc_info=True)