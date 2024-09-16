import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.events import NewMessage

sys.path.insert(0, os.getcwd())
from configs.logging import init_logging
from utils.message_helpers import MessageBuilder
from utils.repo.interface import Repository, repository_factory
from utils.tg_helpers import get_telethon_session


def configure() -> tuple[dict[str, Any], list[dict]]:

    load_dotenv(dotenv_path=Path("/run/secrets/config"))

    with open(os.getenv("TG_KEYS_FILE"), "r") as f:
        keys = json.load(f)

    logger.info("Fetching channels list...")
    chats_repository = repository_factory(
        repo_type=os.getenv("CHANNEL_REPO"),
        table_name=os.getenv("CHANNEL_TABLE"),
        collection_name=os.getenv("CHANNEL_COLLECTION"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWD"),
        ip=os.getenv("DB_IP"),
        port=os.getenv("DB_PORT"),
    )
    chats_repository.connect()
    chats = chats_repository.get_all()
    chats_repository.disconnect()
    logger.info("Channels list loaded.")

    return keys, chats


async def live_parser(
    tg_client: TelegramClient, chats: list[dict], message_repository: Repository
) -> None:

    await tg_client.start()
    logger.info("Telegram Client started.")

    logger.info(f"Parsing data from {len(chats)} chats...")

    chat_ids = [chat["id"] for chat in chats]

    @tg_client.on(
        NewMessage(
            chats=chat_ids,
            # commented out so that both incoming and outgoing messages are parsed
            # useful for testing: just send some message to yourself
            # incoming=True
        )
    )
    async def handler(event: NewMessage.Event) -> None:
        # parse only messages with text, though images may also be of interest
        if event.message.message != "":  # tbh messages with len 1 are useless too
            builder = (
                MessageBuilder(event.message, chats=chats)
                .extract_text()
                .extract_dialog_name()
                .extract_forwards()
            )
            document = await builder.build()

            response = message_repository.put_one(document)
            logger.info(
                f'Added message {document["msg_id"]} '
                f'from chat {document["chat_id"]}. ' + response
            )

    await tg_client.run_until_disconnected()


def main() -> None:

    keys, chats = configure()

    message_repository = repository_factory(
        repo_type=os.getenv("MESSAGE_REPO"),
        table_name=os.getenv("MESSAGE_TABLE"),
        collection_name=os.getenv("MESSAGE_COLLECTION"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWD"),
        ip=os.getenv("DB_IP"),
        port=os.getenv("DB_PORT"),
    )
    logger.info("Connecting to database...")
    message_repository.connect()
    logger.info("Connection established.")

    session = get_telethon_session(
        db=keys["session_name"],
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWD"),
        ip=os.getenv("DB_IP"),
        port=os.getenv("DB_PORT"),
    )

    logger.info("Initializing Telegram Client...")
    tg_client = TelegramClient(
        session, keys["api_id"], keys["api_hash"], catch_up=True
    )

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(live_parser(tg_client, chats, message_repository))
    except KeyboardInterrupt:
        message_repository.disconnect()
        pass  # TelegramClient connection autocloses on SIGINT


if __name__ == "__main__":
    init_logging()
    logger = logging.getLogger(__name__)

    main()
