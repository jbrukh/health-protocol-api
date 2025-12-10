import logging
import logging.config
import os
import json


class JsonFormatter(logging.Formatter):
    """Simple JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        base = {
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            base["stack"] = record.stack_info

        # Merge any extra fields (adapter extra appears in record.__dict__)
        for key, value in record.__dict__.items():
            if key not in base and key not in (
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            ):
                try:
                    json.dumps(value)  # ensure serializable
                    base[key] = value
                except Exception:
                    base[key] = str(value)
        return json.dumps(base, ensure_ascii=False)


def configure_logging():
    """Configure JSON logging for uvicorn and app loggers."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handlers = ["default"]

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "app.logging_config.JsonFormatter",
                },
            },
            "handlers": {
                "default": {
                    "level": level,
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": handlers, "level": level, "propagate": False},
                "uvicorn.error": {"handlers": handlers, "level": level, "propagate": False},
                "uvicorn.access": {"handlers": handlers, "level": level, "propagate": False},
                "app": {"handlers": handlers, "level": level, "propagate": False},
            },
            "root": {"handlers": handlers, "level": level},
        }
    )
