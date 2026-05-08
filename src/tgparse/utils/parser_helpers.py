import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from telethon import TelegramClient

from tgparse.utils.repo.interface import Repository, repository_factory

if TYPE_CHECKING:
    from utils.channel_helpers import TypeCompact

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RepoSpec:
    repo_type: str
    table_name: str
    collection_name: str | None = None

    def __post_init__(self) -> None:
        if not self.collection_name:
            object.__setattr__(self, 'collection_name', self.table_name)


def get_repository(repo_spec: RepoSpec) -> Repository:
    repository = repository_factory(
        repo_type=repo_spec.repo_type,
        table_name=repo_spec.table_name,
        collection_name=repo_spec.collection_name,
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWD'),
        ip=os.getenv('DB_IP'),
        port=os.getenv('DB_PORT'),
    )
    repository.connect()
    return repository


def get_chats_to_parse(repo_spec: RepoSpec) -> list[TypeCompact]:
    logger.info('Fetching channels list...')
    chats_repository = get_repository(repo_spec)
    chats = chats_repository.get_all()
    chats_repository.disconnect()
    logger.info('Channels list loaded.')
    return chats


def get_telegram_client(session_type='sqlite') -> TelegramClient:
    session_name = os.getenv('SESSION_NAME')

    if session_type == 'sqlite':
        session = session_name
    elif session_type == 'mongodb':
        from utils.tg_helpers import get_telemongo_session  # NOTE: avoids unnecessary dependencies

        session = get_telemongo_session(
            db=session_name,
            user=os.getenv('DB_USER'),
            passwd=os.getenv('DB_PASSWD'),
            ip=os.getenv('DB_IP'),
            port=os.getenv('DB_PORT'),
        )

    logger.info('Initializing Telegram Client...')
    return TelegramClient(
        session=session,
        api_id=os.getenv('API_ID'),
        api_hash=os.getenv('API_HASH'),
        catch_up=True,
    )
