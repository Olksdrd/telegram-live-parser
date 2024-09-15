import importlib
from enum import StrEnum
from typing import Optional, Protocol


class Repository[T](Protocol):
    """Repository of objects of generic type T
    1. Connect
    2. Check connection
    3. Create table (optional)
    4. Put one/many
    5. Get all
    6. Close connection
    """

    def connect(self) -> None:
        pass

    def _is_connected(self) -> bool:
        pass

    def disconnect(self) -> None:
        pass

    def put_one(self, object: T) -> str:
        pass

    def put_many(self, objects: list[T]) -> str:
        pass

    # def get(self, id: str) -> T:
    #     pass

    def get_all(self) -> list[T]:
        pass


class RepositoryType(StrEnum):
    MONGODB = "mongo"
    DYNAMODB = "dynamo"
    LOCAL_STORAGE = "local"
    CLI = "cli"


def repository_factory(
    repo_type: str,
    table_name: Optional[str],
    collection_name: Optional[str] = None,
    user: Optional[str] = None,
    passwd: Optional[str] = None,
    ip: Optional[str] = None,
    port: Optional[str | int] = None,
    region: Optional[str] = "eu-central-1",
) -> Repository:
    # allows to avoid installing unnecessary dependencies
    # ! repo_type should be one of the options from the Enum above
    # load corresponding module from .utils/repo directory
    repo_module = importlib.import_module(f"utils.repo.{repo_type.lower()}")
    # get repository class by name
    repo = getattr(repo_module, f"{repo_type.capitalize()}Repository")
    # unused kwargs will be ignored
    return repo(
        table_name=table_name,
        collection_name=collection_name,
        user=user,
        passwd=passwd,
        ip=ip,
        port=port,
        region=region,
    )
