import json
from collections.abc import Mapping


class CliRepository:
    def __init__(self, **kwargs) -> None:
        pass

    def connect(self) -> None:
        pass

    def _is_connected(self) -> bool:
        pass

    def disconnect(self) -> None:
        pass

    def put_one(self, object: Mapping) -> str:
        doc = {k: v for k, v in object.items() if v}
        print(json.dumps(doc, default=str, ensure_ascii=False))
        return "-" * 40

    def put_many(self, objects: list[Mapping]) -> str:
        docs = [{k: v for k, v in doc.items() if v} for doc in objects]
        print(json.dumps(docs, default=str, ensure_ascii=False))
        return "-" * 40

    # def get(self, id: str) -> T:
    #     pass

    def get_all(self) -> list[Mapping]:
        # ? read from STDIN?
        raise Exception("How is it supposed to work?")
