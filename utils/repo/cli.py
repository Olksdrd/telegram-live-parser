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
        doc = {k: v for k, v in object.items() if v}
        print(json.dumps(doc, default=str, ensure_ascii=False))
        return '-' * 40

    def put_many(self, objects: list[CompactMessage]) -> str:
        docs = [{k: v for k, v in doc.items() if v} for doc in objects]
        print(json.dumps(docs, default=str, ensure_ascii=False))
        return '-' * 40

    # def get(self, id: str) -> T:
        ...

    # def get_all(self) -> list[T]:
        ...
