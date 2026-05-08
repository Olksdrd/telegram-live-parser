import atexit
import logging
import os
from logging.config import dictConfig
from typing import Any, override

LOGS_DIR = './logs/'
CONTAINER_RUNTIME = True if os.getenv('CONTAINER_RUNTIME') == 'true' else False


class InfoFilter(logging.Filter):
    def __init__(self) -> None:
        super().__init__()

    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO


def generate_log_config(min_log_level: str) -> dict[str, Any]:
    handlers_list = ['stdout', 'stderr', 'file']

    handlers_specification = {
        'stdout': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': min_log_level,
            'stream': 'ext://sys.stdout',
            'filters': ['info'],
        },
        'stderr': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'WARNING',
            'stream': 'ext://sys.stderr',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'detailed',
            'level': 'DEBUG',
            'filename': f'{LOGS_DIR}/logfile.log',
            'maxBytes': 10_000_000,  # 10 Mb
            'backupCount': 5,
        },
        'queue_handler': {  # needs Python>=3.12
            'class': 'logging.handlers.QueueHandler',
            'handlers': handlers_list,
            'respect_handler_level': True,
        },
    }

    # no point in a logfile inside a container
    if CONTAINER_RUNTIME:
        handlers_specification.pop('file')
        handlers_list.remove('file')

    log_config = {
        'version': 1,  # the only possible value
        'disable_existing_loggers': False,
        'filters': {
            'info': {
                '()': InfoFilter,
            },
        },
        'formatters': {
            'standard': {'format': '%(asctime)s [%(levelname)s]: %(message)s'},
            'detailed': {
                'format': '%(asctime)s [%(levelname)s|%(module)s|L%(lineno)s]: %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S%z',
            },
        },
        'handlers': handlers_specification,
        'loggers': {
            'root': {
                'handlers': ['queue_handler'],
                'level': min_log_level,
                'propagate': True,
            },
        },
    }
    return log_config


def filter_external_logs(min_log_level_num: int) -> None:
    # NOTE: {DEBUG = 10, INFO = 20, WARNING = 30, ERROR = 40, CRITICAL = 50}
    logger_blocklist = {
        'asyncio': max(logging.getLevelName('INFO'), min_log_level_num),
        'telethon': max(logging.getLevelName('INFO'), min_log_level_num),
    }

    for module, min_log_level in logger_blocklist.items():
        logging.getLogger(module).setLevel(min_log_level)


def init_logging(min_log_level: str = 'DEBUG') -> None:
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    log_config = generate_log_config(min_log_level)
    dictConfig(log_config)

    filter_external_logs(logging.getLevelName(min_log_level))

    # start a thread for a queue handler so it doesn't block useful work
    queue_handler = logging.getHandlerByName('queue_handler')
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)
