import asyncio
import json
import logging
import os
import sys
from typing import Any

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import TypeInputPeer

sys.path.insert(0, os.getcwd())
from utils.channel_helpers import TypeCompact, entitity_info_request, get_compact_name
from utils.message_helpers import MessageBuilder
from utils.repo.interface import Repository, repository_factory


def configure() -> tuple[dict[str, Any], list[dict]]:

    load_dotenv("./env/config.env")

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s"
    )

    with open(os.getenv("TG_KEYS_FILE"), "r") as f:
        keys = json.load(f)

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

    return keys, chats


async def get_dialog(
    client: TelegramClient, dialog: TypeCompact
) -> TypeCompact | TypeInputPeer:
    try:
        chat = await client.get_input_entity(dialog["id"])
    except ValueError:
        chat = await entitity_info_request(client, dialog)
    return chat


async def parse_channel(
    client: TelegramClient,
    message_repository: Repository,
    dialog: dict[TypeCompact],
) -> None:
    if not client.is_connected():
        await client.connect()

    chat = await get_dialog(client, dialog)
    if chat is None:
        logging.warning(f"Couldn't find chat {dialog['id']}. Skipping...")
        return

    logging.info(f"Retreiving data from {get_compact_name(dialog)}.")

    docs = []
    async for message in client.iter_messages(chat, limit=2):

        # don't chain them since async ones return coroutines and not builders
        builder = MessageBuilder(message, chats=[dialog]).extract_text()
        builder = builder.extract_dialog_name()
        builder = await builder.extract_engagements()
        builder = builder.extract_forwards()
        doc = await builder.build()

        docs.append(doc)
        # message_repository.put_one(doc)

    message_repository.put_many(docs)
    logging.info(f"{len(docs)} messages retreived.")


async def amain() -> None:

    keys, dialogs = configure()

    message_repository = repository_factory(
        repo_type=os.getenv("MESSAGE_REPO"),
        table_name=os.getenv("MESSAGE_TABLE"),
        collection_name=os.getenv("MESSAGE_COLLECTION"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWD"),
        ip=os.getenv("DB_IP"),
        port=os.getenv("DB_PORT"),
    )
    logging.info("Connecting to database...")
    message_repository.connect()
    logging.info("Connection established.")

    logging.info("Initializing Telegram Client...")
    client = TelegramClient(
        # keys["session_name"],
        "anon",
        keys["api_id"],
        keys["api_hash"],
    )
    client.loop.set_debug(True)
    await client.start()
    logging.info("Telegram Client started.")

    # not the most effective async :(
    for dialog in dialogs:
        await parse_channel(client, message_repository, dialog)

    message_repository.disconnect()


if __name__ == "__main__":
    asyncio.run(amain())
