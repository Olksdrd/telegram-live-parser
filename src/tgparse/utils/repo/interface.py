import importlib
import logging
import os
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from utils.channel_helpers import TypeCompactEntity

logger = logging.getLogger(__name__)


class Repository[T](Protocol):
    """
    Repository of objects of generic type T
    1. Connect
    2. Check connection
    3. Create table (optional)
    4. Put one/many
    5. Get all
    6. Close connection.
    """

    def connect(self) -> None:
        pass

    def _is_connected(self) -> bool:
        pass

    def disconnect(self) -> None:
        pass

    def put_one(self, datum: T) -> str:
        pass

    def put_many(self, data: list[T]) -> str:
        pass

    # def get(self, id: str) -> T:
    #     pass

    def get_all(self) -> list[T]:
        pass


@dataclass(frozen=True)
class RepoSpec:
    repo_type: str
    table_name: str | None
    collection_name: str | None = None

    def __post_init__(self) -> None:
        if not self.collection_name:
            object.__setattr__(self, 'collection_name', self.table_name)


class RepositoryType(StrEnum):
    CLI = 'cli'
    JSON_STORAGE = 'json'
    MONGODB = 'mongo'
    DYNAMODB = 'dynamo'


def repository_factory(
    repo_spec: RepoSpec,
    user: str | None = None,
    passwd: str | None = None,
    ip: str | None = None,
    port: str | int | None = None,
    region: str | None = 'eu-central-1',
) -> Repository:
    # allows to avoid installing unnecessary dependencies
    repo_type = RepositoryType.lower(repo_spec.repo_type)
    # load corresponding module from ../utils/repo directory
    repo_module = importlib.import_module(f'tgparse.utils.repo.{repo_type}')
    # get repository class by name
    repo = getattr(repo_module, f'{RepositoryType.capitalize(repo_type)}Repository')
    # unused kwargs will be ignored
    return repo(
        table_name=repo_spec.table_name,
        collection_name=repo_spec.collection_name,
        user=user,
        passwd=passwd,
        ip=ip,
        port=port,
        region=region,
    )


def get_repository(repo_spec: RepoSpec) -> Repository:
    repository = repository_factory(
        repo_spec=repo_spec,
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWD'),
        ip=os.getenv('DB_IP'),
        port=os.getenv('DB_PORT'),
    )
    repository.connect()
    return repository


def get_chats_to_parse(repo_spec: RepoSpec) -> list[TypeCompactEntity]:
    logger.info('Fetching channels list...')
    chats_repository = get_repository(repo_spec)
    chats = chats_repository.get_all()
    chats_repository.disconnect()
    logger.info('Channels list loaded.')
    return chats
