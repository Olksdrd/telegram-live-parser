from enum import StrEnum
import importlib
import os
from typing import Optional, Protocol

from dotenv import load_dotenv

load_dotenv('./env/config.env')


class RepositoryType(StrEnum):
    MONGODB = 'mongodb'
    DYNAMODB = 'dynamodb'
    LOCAL_STORAGE = 'local'
    CLI = 'cli'


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
        ...

    def _is_connected(self) -> bool:
        ...

    def disconnect(self) -> None:
        ...

    def put_one(self, object: T) -> str:
        ...

    # def put_many(self, objects: list[T]) -> str:
        ...

    # def get(self, id: str) -> T:
        ...

    # def get_all(self) -> list[T]:
        ...


def repository_factory(
    repo_type: str = '',
    table_name: Optional[str] = 'cli',
    collection_name: Optional[str] = None,
    user: Optional[str] = None,
    passwd: Optional[str] = None,
    ip: Optional[str] = None,
    port: Optional[str | int] = None
) -> Repository:
    if repo_type == '':
        repo_type = os.getenv('REPOSITORY_TYPE')

    # ! repo in Enum should have the same name as the corresponding .py file
    repo = importlib.import_module(f'utils.repo.{repo_type}')

    if repo_type == RepositoryType.MONGODB:
        return repo.MongoRepository(
            table_name=table_name,
            collection_name=collection_name,
            user=user,
            passwd=passwd,
            ip=ip,
            port=port
        )
    elif repo_type == RepositoryType.DYNAMODB:
        return repo.DynamoRepository(
            table_name=table_name,
        )
    elif repo_type == RepositoryType.CLI:
        return repo.Repository()
    elif repo_type == RepositoryType.LOCAL_STORAGE:
        raise NotImplementedError
    else:
        raise ValueError
