import asyncio
import logging
import os
import sys

from telethon import TelegramClient
from telethon.tl.types import TypeInputPeer

sys.path.insert(0, os.getcwd())
from configs.logging import init_logging
from parser_helpers import get_chats_to_parse, get_message_repo, get_telegram_client
from utils.channel_helpers import TypeCompact, entitity_info_request
from utils.message_helpers import MessageBuilder
from utils.repo.interface import Repository

logger = logging.getLogger(__name__)


async def get_dialog(
    client: TelegramClient, dialog: TypeCompact
) -> TypeCompact | TypeInputPeer | None:
    try:
        chat = await client.get_input_entity(dialog["id"])
    except ValueError:
        chat = await entitity_info_request(client, dialog)
    return chat


async def parse_channel(
    client: TelegramClient,
    message_repository: Repository,
    dialog: TypeCompact,
) -> None:
    if not client.is_connected():
        await client.connect()

    chat = await get_dialog(client, dialog)
    if chat is None:
        logger.warning(f"Couldn't find chat {dialog['id']}. Skipping...")
        return

    logger.info(f"Retreiving data from {dialog['id']}.")

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
    logger.info(f"{len(docs)} messages retreived.")


async def amain() -> None:

    dialogs = get_chats_to_parse()

    message_repository = get_message_repo()

    client = get_telegram_client(session_type="mongodb")
    client.loop.set_debug(True)
    logger.info("Telegram Client started.")

    # not the most effective async :(
    for dialog in dialogs:
        await parse_channel(client, message_repository, dialog)

    message_repository.disconnect()


if __name__ == "__main__":
    init_logging()

    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass
