import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

sys.path.insert(0, os.getcwd())
from utils.channel_helpers import TypeCompact
from utils.repo.interface import Repository, repository_factory
from utils.tg_helpers import get_telemongo_session

logger = logging.getLogger(__name__)

load_dotenv(dotenv_path=Path(os.getenv("CONFIG_PATH")))


def get_message_repo() -> Repository:

    message_repository = repository_factory(
        repo_type=os.getenv("MESSAGE_REPO"),
        table_name=os.getenv("MESSAGE_TABLE"),
        collection_name=os.getenv("MESSAGE_COLLECTION"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWD"),
        ip=os.getenv("DB_IP"),
        port=os.getenv("DB_PORT"),
    )
    message_repository.connect()

    return message_repository


def get_channel_repo() -> Repository:

    channel_repository = repository_factory(
        repo_type=os.getenv("CHANNEL_REPO"),
        table_name=os.getenv("CHANNEL_TABLE"),
        collection_name=os.getenv("CHANNEL_COLLECTION"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWD"),
        ip=os.getenv("DB_IP"),
        port=os.getenv("DB_PORT"),
    )
    channel_repository.connect()

    return channel_repository


def get_chats_to_parse() -> list[TypeCompact]:

    logger.info("Fetching channels list...")
    chats_repository = get_channel_repo()
    chats = chats_repository.get_all()
    chats_repository.disconnect()
    logger.info("Channels list loaded.")

    return chats


def get_telegram_client(session_type="sqlite") -> TelegramClient:

    session_name = os.getenv("SESSION_NAME")

    if session_type == "sqlite":
        session = session_name
    elif session_type == "mongodb":
        session = get_telemongo_session(
            db=session_name,
            user=os.getenv("DB_USER"),
            passwd=os.getenv("DB_PASSWD"),
            ip=os.getenv("DB_IP"),
            port=os.getenv("DB_PORT"),
        )

    logger.info("Initializing Telegram Client...")
    client = TelegramClient(
        session=session,
        api_id=os.getenv("API_ID"),
        api_hash=os.getenv("API_HASH"),
        catch_up=True,
    )

    return client
