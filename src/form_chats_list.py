import asyncio
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import Channel, Chat

sys.path.insert(0, os.getcwd())
from utils.channel_helpers import CompactChannel, CompactChat, CompactUser, TypeCompact
from utils.repo.interface import repository_factory


def configure() -> tuple[dict[str, int], list[str]]:
    load_dotenv(dotenv_path=Path("./env/config.env"))

    with open(os.getenv("TG_KEYS_FILE"), "r") as f:
        keys = json.load(f)

    with open(os.getenv("NON_SUBBED_CHANNELS_LIST"), "r") as f:
        non_subscribed_channels = json.load(f)

    return keys, non_subscribed_channels


async def get_subscriptions_list(client: TelegramClient) -> list[TypeCompact]:
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
        print(f"Channel '{name}' not found.")


async def get_non_subscription_channels(
    client: TelegramClient, non_subscribed_channels: list[str]
) -> list[TypeCompact]:
    dialogs_to_parse = []
    for channel_name in non_subscribed_channels:
        channel = await get_channel_by_name(client, name=channel_name)
        dialogs_to_parse.append(channel)

    return dialogs_to_parse


async def amain() -> None:
    keys, non_subscribed_channels = configure()

    repository = repository_factory(
        repo_type=os.getenv("CHANNEL_REPO"),
        table_name=os.getenv("CHANNEL_TABLE"),
        collection_name=os.getenv("CHANNEL_COLLECTION"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWD"),
        ip=os.getenv("DB_IP"),
        port=os.getenv("DB_PORT"),
    )
    repository.connect()

    client = TelegramClient(keys["session_name"], keys["api_id"], keys["api_hash"])
    await client.start()

    dialogs_to_parse = []
    if os.getenv("PARSE_SUBSRIPTIONS") == "yes":
        dialogs_to_parse = await get_subscriptions_list(client)

    dialogs_to_parse += await get_non_subscription_channels(
        client, non_subscribed_channels
    )

    repository.put_many(dialogs_to_parse)
    print(f"Info for {len(dialogs_to_parse)} chats saved.")

    repository.disconnect()


if __name__ == "__main__":
    asyncio.run(amain())
