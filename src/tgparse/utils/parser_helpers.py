import logging
import os

from telethon import TelegramClient

from typing import TYPE_CHECKING

from utils.repo.interface import Repository, repository_factory

if TYPE_CHECKING:
    from utils.channel_helpers import TypeCompact

logger = logging.getLogger(__name__)


def get_message_repository(repo_type: str, table_name: str) -> Repository:
    message_repository = repository_factory(
        repo_type=repo_type,
        table_name=table_name,
        collection_name=os.getenv('MESSAGE_COLLECTION'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWD'),
        ip=os.getenv('DB_IP'),
        port=os.getenv('DB_PORT'),
    )
    message_repository.connect()
    return message_repository


def get_chats_repository(repo_type: str, table_name: str) -> Repository:
    chats_repository = repository_factory(
        repo_type=repo_type,
        table_name=table_name,
        collection_name=os.getenv('CHATS_COLLECTION'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWD'),
        ip=os.getenv('DB_IP'),
        port=os.getenv('DB_PORT'),
    )
    chats_repository.connect()
    return chats_repository


def get_chats_to_parse(repo_type: str, table_name: str) -> list[TypeCompact]:
    logger.info('Fetching channels list...')
    chats_repository = get_chats_repository(repo_type, table_name)
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
