"""
Use to save messages to json locally and then pipe them into jq.
Useful for investigating parsing results and looking for edge cases.
"""

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = logging.getLogger(__name__)


class JsonRepository:
    def __init__(self, table_name: str | None = None, **kwargs) -> None:
        self.output_path = Path(table_name).absolute()

    def connect(self) -> None:
        logger.info('Connecting to database...')
        if not self.output_path.exists():
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            self.output_path.touch(exist_ok=True)
        logger.info('Connection established.')

    def _is_connected(self) -> bool:
        pass

    def disconnect(self) -> None:
        logger.info('Database connection closed.')

    def put_one(self, object: Mapping) -> str:
        doc = {k: v for k, v in object.items() if v}
        if not doc:
            logger.warning('Document was empty. Skipping...')
            return None
        with open(self.output_path, mode='r+') as file:
            try:
                file.seek(0, 2)
                position = file.tell() - 1
                file.seek(position)
                file.write(f',{json.dumps(doc, default=str, ensure_ascii=False)}]')
            except ValueError:
                file.write(f'[{json.dumps(doc, default=str, ensure_ascii=False)}]')
        return 'Saved 1 document.'

    def put_many(self, objects: list[Mapping]) -> str:
        docs = [{k: v for k, v in doc.items() if v} for doc in objects]
        non_empty_docs = [doc for doc in docs if doc]
        if docs != non_empty_docs:
            num_of_empty_docs = len(docs) - len(non_empty_docs)
            logger.warning(f'Skipping {num_of_empty_docs} empty documents...')
        with open(self.output_path, 'w') as f:
            json.dump(non_empty_docs, f, default=str, ensure_ascii=False)
        return f'Saved {len(non_empty_docs)} documents.'

    # def get(self, id: str) -> T:
    #     pass

    def get_all(self) -> list[Mapping]:
        with open(self.output_path) as f:
            return json.load(f)

