"""Good for printing a dozen of messages to STDOUT for quick testing."""

import fcntl
import json
import logging
import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class CliRepository:
    def __init__(self, **kwargs) -> None:
        pass

    def connect(self) -> None:
        logger.info('Connecting to database...')
        logger.info('Connection established.')

    def _is_connected(self) -> bool:
        pass

    def disconnect(self) -> None:
        logger.info('Database connection closed.')

    def put_one(self, object: Mapping) -> str:
        doc = {k: v for k, v in object.items() if v}
        print(
            json.dumps(doc, default=str, ensure_ascii=False),
            flush=True,
            file=sys.stdout,
        )
        return 'Processed 1 document.'

    def put_many(self, objects: list[Mapping]) -> str:
        docs = [{k: v for k, v in doc.items() if v} for doc in objects]
        print(
            json.dumps(docs, default=str, ensure_ascii=False),
            flush=True,
            file=sys.stdout,
        )
        return f'Processed {len(docs)} documents.'

    # def get(self, id: str) -> T:
    #     pass

    def get_all(self) -> list[Mapping]:
        # NOTE: don't wait for input if it's not provided at the beginning
        # See: https://stackoverflow.com/questions/26263636/how-to-check-potentially-empty-stdin-without-waiting-for-input  # noqa F501
        fd: int = sys.stdin.fileno()
        old_flags: int = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, old_flags | os.O_NONBLOCK)
        input_text = sys.stdin.buffer.raw.read()
        input_obj = json.loads(input_text)
        if type(input_obj) is not list:
            input_obj = [input_obj]
        return input_obj
