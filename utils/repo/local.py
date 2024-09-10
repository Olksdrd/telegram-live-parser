from dataclasses import asdict
import json
import os
from typing import Optional

from utils.message_helpers import CompactMessage


class LocalRepository:
    def __init__(
        self,
        table_name: Optional[str] = None
    ) -> None:
        self.path = f'./{table_name}.json'

    def connect(self) -> None:
        # pass
        if not os.path.exists(self.path):
            os.mknod(self.path)

    def _is_connected(self) -> bool:
        pass

    def disconnect(self) -> None:
        pass

    def put_one(self, object: CompactMessage) -> str:
        with open(self.path, mode="r+") as file:
            try:
                file.seek(0, 2)
                position = file.tell() - 1
                file.seek(position)
                file.write(',{}]'.format(json.dumps(
                    asdict(object),
                    default=str,
                    ensure_ascii=False
                )))
            except ValueError:
                file.write('[{}]'.format(json.dumps(
                    asdict(object),
                    default=str,
                    ensure_ascii=False
                )))
        return '-' * 40

    def put_many(self, objects: list[CompactMessage]) -> str:
        docs = [asdict(obj) for obj in objects]
        with open(self.path, 'w') as f:
            json.dump(docs, f, default=str, ensure_ascii=False)
        return '-' * 40

    # def get(self, id: str) -> T:
        ...

    # def get_all(self) -> list[T]:
        ...
