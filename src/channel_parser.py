import asyncio
import logging
import os
import sys

from telethon import TelegramClient

sys.path.insert(0, os.getcwd())
from configs.logging import init_logging
from parser_helpers import get_chats_to_parse, get_message_repo, get_telegram_client
from utils.channel_helpers import TypeCompact, get_peer_by_id
from utils.message_helpers import MessageBuilder
from utils.repo.interface import Repository

logger = logging.getLogger(__name__)


async def parse_channel(
    client: TelegramClient,
    message_repository: Repository,
    builder: MessageBuilder,
    dialog: TypeCompact,
) -> None:
    if not client.is_connected():
        await client.connect()

    chat = await get_peer_by_id(client, dialog)
    if chat is None:
        logger.warning(f"Couldn't find chat {dialog['id']}. Skipping...")
        return

    logger.info(f"Retreiving data from {dialog['id']}.")

    docs = []
    async for message in client.iter_messages(chat, limit=110, wait_time=2):

        for method in builder.registered_methods:
            await method(message)

        doc = builder.build()

        docs.append(doc)
        message_repository.put_one(doc)

    # message_repository.put_many(docs)
    logger.info(f"{len(docs)} messages retreived.")


async def amain() -> None:

    dialogs = get_chats_to_parse()

    message_repository = get_message_repo()

    client = get_telegram_client(session_type="mongodb")
    client.loop.set_debug(True)
    logger.info("Telegram Client started.")

    builder = MessageBuilder(
        registered_methods=[
            "extract_text",
            "extract_dialog_info",
            "extract_engagements",
            "extract_forward_info",
        ],
        client=client,
        chats=dialogs,
    )

    # not the most effective async :(
    for dialog in dialogs:
        await parse_channel(client, message_repository, builder, dialog)

    message_repository.disconnect()


if __name__ == "__main__":
    init_logging()

    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass
