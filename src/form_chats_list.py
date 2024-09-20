import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

sys.path.insert(0, os.getcwd())
from configs.logging import init_logging
from parser_helpers import get_channel_repo, get_telegram_client
from utils.channel_helpers import CompactChannel, CompactChat, CompactUser, TypeCompact

logger = logging.getLogger(__name__)


def configure() -> list[str]:
    load_dotenv(dotenv_path=Path("./env/config.env"))

    with open(os.getenv("NON_SUBBED_CHANNELS_LIST"), "r") as f:
        non_subscribed_channels = json.load(f)

    return non_subscribed_channels


async def get_subscriptions_list(client: TelegramClient) -> list[TypeCompact]:
    logger.info("Iterating over subscriptions list...")
    dialogs = client.iter_dialogs()

    dialogs_to_parse = []
    async for dialog in dialogs:
        if dialog.is_channel:
            compact_dialog = CompactChannel(
                id=dialog.entity.id,
                name=dialog.entity.username,
                title=dialog.entity.title,
                participants_count=dialog.entity.participants_count,
                creation_date=dialog.entity.date,
            )
        elif dialog.is_user:
            compact_dialog = CompactUser(
                id=dialog.entity.id,
                username=dialog.entity.username,
                first_name=dialog.entity.first_name,
                last_name=dialog.entity.last_name,
            )
        elif isinstance(dialog.entity, Chat):
            parent_peer = dialog.entity.migrated_to
            compact_dialog = CompactChat(
                id=dialog.entity.id,
                title=dialog.entity.title,
                creation_date=dialog.entity.date,
                parent_channel=parent_peer.channel_id if parent_peer else None,
            )
        else:
            # ignore ChatForbidden and megagroups for now
            pass

        if compact_dialog:
            dialogs_to_parse.append(
                {key: val for key, val in compact_dialog.items() if val is not None}
            )

    logger.info(f"{len(dialogs_to_parse)} dialogs added.")
    return dialogs_to_parse


async def get_channel_by_name(
    client: TelegramClient, name: str
) -> CompactChannel | None:
    if not client.is_connected():
        await client.connect()

    try:
        channel: Channel = await client.get_entity(name)
        return CompactChannel(
            id=channel.id,
            name=channel.username,
            title=channel.title,
            participants_count=channel.participants_count,
            creation_date=channel.date,
        )
    except ValueError:
        logger.warning(f"Channel '{name}' not found.")


async def get_non_subscription_channels(
    client: TelegramClient, non_subscribed_channels: list[str]
) -> list[TypeCompact]:
    logger.info("Adding additional public channels...")

    dialogs_to_parse = []
    for channel_name in non_subscribed_channels:
        channel = await get_channel_by_name(client, name=channel_name)
        dialogs_to_parse.append(channel)

    return dialogs_to_parse


async def amain() -> None:
    non_subscribed_channels = configure()

    repository = get_channel_repo()

    client = get_telegram_client()

    await client.start()
    logger.info("Telegram Client started.")

    dialogs_to_parse = []
    if os.getenv("PARSE_SUBSRIPTIONS") == "yes":
        dialogs_to_parse = await get_subscriptions_list(client)

    dialogs_to_parse += await get_non_subscription_channels(
        client, non_subscribed_channels
    )

    repository.put_many(dialogs_to_parse)
    logger.info(f"Info for {len(dialogs_to_parse)} chats saved.")

    repository.disconnect()


if __name__ == "__main__":
    init_logging()

    asyncio.run(amain())
