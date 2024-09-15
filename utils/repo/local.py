import json
import os
from collections.abc import Mapping
from typing import Optional


class LocalRepository:
    def __init__(self, table_name: Optional[str] = None, **kwargs) -> None:
        self.path = f"./{table_name}.json"

    def connect(self) -> None:
        if not os.path.exists(self.path):
            os.mknod(self.path)

    def _is_connected(self) -> bool:
        pass

    def disconnect(self) -> None:
        pass

    def put_one(self, object: Mapping) -> str:
        doc = {k: v for k, v in object.items() if v}
        with open(self.path, mode="r+") as file:
            try:
                file.seek(0, 2)
                position = file.tell() - 1
                file.seek(position)
                file.write(
                    ",{}]".format(json.dumps(doc, default=str, ensure_ascii=False))
                )
            except ValueError:
                file.write(
                    "[{}]".format(json.dumps(doc, default=str, ensure_ascii=False))
                )
        return "-" * 40

    def put_many(self, objects: list[Mapping]) -> str:
        docs = [{k: v for k, v in doc.items() if v} for doc in objects]
        with open(self.path, "w") as f:
            json.dump(docs, f, default=str, ensure_ascii=False)
        return "-" * 40

    # def get(self, id: str) -> T:
    #     pass

    # def get_all(self) -> list[T]:
    #     pass
