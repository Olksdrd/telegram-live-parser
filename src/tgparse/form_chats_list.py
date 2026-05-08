import asyncio
import json
import logging
import os

from typing import TYPE_CHECKING

from tgparse.utils.logging import init_logging
from tgparse.utils.parser_helpers import get_chats_repository, get_telegram_client
from tgparse.utils.channel_helpers import (
    get_non_subscription_entities,
    get_subscriptions_list,
)

if TYPE_CHECKING:
    from telethon import TelegramClient

    from tgparse.utils.repo.interface import Repository

logger = logging.getLogger(__name__)


def load_channels_list(list_path: str) -> list[str]:
    if not list_path:
        return []
    with open(list_path) as f:
        non_subscribed_channels = json.load(f)
    return list(set(non_subscribed_channels))


async def chat_metadata_parser(
    repository: Repository,
    client: TelegramClient,
    list_path: str,
    parse_subscriptions: bool,
) -> None:
    non_subscribed_channels = load_channels_list(list_path)

    await client.start()
    logger.info('Telegram Client started.')

    dialogs_to_parse = []
    if parse_subscriptions:
        dialogs_to_parse = await get_subscriptions_list(client)

    dialogs_to_parse += await get_non_subscription_entities(client, non_subscribed_channels)

    repository.put_many(dialogs_to_parse)
    logger.info(f'Info for {len([dialog for dialog in dialogs_to_parse if dialog])} chats saved.')
    await client.disconnect()


def start_chat_metadata_parser(
    session_backend: str,
    chats_repository: str,
    chats_path: str,
    additional_channels=str,
    parse_subscriptions=bool,
) -> None:
    print('Starting')
    repository = get_chats_repository(repo_type=chats_repository, table_name=chats_path)
    tg_client = get_telegram_client(session_type=session_backend)

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(chat_metadata_parser(
            repository,
            tg_client,
            additional_channels,
            parse_subscriptions,
        ))
    except KeyboardInterrupt:
        pass  # TelegramClient connection autocloses on SIGINT
    finally:
        repository.disconnect()


if __name__ == '__main__':
    init_logging()

    parse_subcriptions = True if os.getenv('PARSE_SUBSCRIPTIONS') == 'yes' else False
    start_chat_metadata_parser(
        session_backend=os.getenv('SESSION_DB_TYPE'),
        chats_repository=os.getenv('CHATS_REPO'),
        chats_path=os.getenv('CHATS_TABLE'),
        additional_channels=os.getenv('NON_SUBBED_CHANNELS_LIST'),
        parse_subscriptions=parse_subcriptions,
    )
