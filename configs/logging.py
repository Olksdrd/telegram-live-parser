import atexit
import logging
import os
from logging.config import dictConfig
from typing import override


class InfoFilter(logging.Filter):
    def __init__(self) -> None:
        super(InfoFilter, self).__init__()

    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO


handlers_list = ["stdout", "stderr", "file"]

handlers = {
    "stdout": {
        "class": "logging.StreamHandler",
        "formatter": "standard",
        "level": "INFO",
        "stream": "ext://sys.stdout",
        "filters": ["info"],
    },
    "stderr": {
        "class": "logging.StreamHandler",
        "formatter": "standard",
        "level": "WARNING",
        "stream": "ext://sys.stderr",
    },
    "file": {
        "class": "logging.handlers.RotatingFileHandler",
        "formatter": "detailed",
        "level": "DEBUG",
        "filename": "configs/logfile.log",
        "maxBytes": 10_000_000,  # 10 Mb
        "backupCount": 5,
    },
    "queue_handler": {  # needs Python>=3.12
        "class": "logging.handlers.QueueHandler",
        "handlers": handlers_list,
        "respect_handler_level": True,
    },
}

if os.getenv("HOME") == "/home/docker":
    print('inside if')
    handlers.pop("file")
    handlers_list.remove("file")


log_config = {
    "version": 1,  # the only possible value
    "disable_existing_loggers": False,
    "filters": {
        "info": {
            "()": InfoFilter,
        }
    },
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s]: %(message)s"},
        "detailed": {
            "format": "%(asctime)s [%(levelname)s|%(module)s|L%(lineno)s]: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z",
        },
    },
    "handlers": handlers,
    "loggers": {
        "root": {
            "handlers": ["queue_handler"],
            "level": "INFO",
            "propagate": True,
        }
    },
}


def init_logging():
    dictConfig(log_config)

    # start a thread for a queue handler so it doesn't block useful work
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
