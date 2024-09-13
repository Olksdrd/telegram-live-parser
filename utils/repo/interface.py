import importlib
from enum import StrEnum
from typing import Optional, Protocol


class RepositoryType(StrEnum):
    MONGODB = "mongodb"
    DYNAMODB = "dynamodb"
    LOCAL_STORAGE = "local"
    CLI = "cli"


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

    # def get_all(self) -> list[T]:
    #     pass


def repository_factory(
    repo_type: str,
    table_name: Optional[str] = "cli",
    collection_name: Optional[str] = None,
    user: Optional[str] = None,
    passwd: Optional[str] = None,
    ip: Optional[str] = None,
    port: Optional[str | int] = None,
) -> Repository:

    # ! repo in Enum should have the same name as the corresponding .py file
    repo = importlib.import_module(f"utils.repo.{repo_type}")

    if repo_type == RepositoryType.MONGODB:
        return repo.MongoRepository(
            table_name=table_name,
            collection_name=collection_name,
            user=user,
            passwd=passwd,
            ip=ip,
            port=port,
        )
    elif repo_type == RepositoryType.DYNAMODB:
        return repo.DynamoRepository(
            table_name=table_name,
        )
    elif repo_type == RepositoryType.CLI:
        return repo.CLIRepository()
    elif repo_type == RepositoryType.LOCAL_STORAGE:
        return repo.LocalRepository(table_name=table_name)
    else:
        raise ValueError
