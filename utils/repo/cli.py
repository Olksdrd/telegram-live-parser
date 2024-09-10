from dataclasses import asdict
import json

from utils.message_helpers import CompactMessage


class CLIRepository:

    def connect(self) -> None:
        pass

    def _is_connected(self) -> bool:
        pass

    def disconnect(self) -> None:
        pass

    def put_one(self, object: CompactMessage) -> str:
        print(json.dumps(asdict(object), default=str, ensure_ascii=False))
        return '-' * 40

    def put_many(self, objects: list[CompactMessage]) -> str:
        docs = [asdict(obj) for obj in objects]
        print(json.dumps(docs, default=str, ensure_ascii=False))
        return '-' * 40

    # def get(self, id: str) -> T:
        ...

    # def get_all(self) -> list[T]:
        ...
