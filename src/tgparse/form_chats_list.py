import asyncio
import logging
import os
from typing import TYPE_CHECKING

from tgparse.utils.channel_helpers import (
    get_non_subscription_entities,
    get_subscriptions_list,
)
from tgparse.utils.logging import init_logging
from tgparse.utils.parser_helpers import (
    RepoSpec,
    get_repository,
    get_telegram_client,
)

if TYPE_CHECKING:
    from telethon import TelegramClient

    from tgparse.utils.repo.interface import Repository

logger = logging.getLogger(__name__)


async def chat_metadata_parser(
    input_repository: Repository,
    output_repository: Repository,
    client: TelegramClient,
    parse_subscriptions: bool,
) -> None:
    non_subscribed_channels = input_repository.get_all()
    input_repository.disconnect()

    await client.start()
    logger.info('Telegram Client started.')

    dialogs_to_parse = []
    if parse_subscriptions:
        dialogs_to_parse = await get_subscriptions_list(client)

    dialogs_to_parse += await get_non_subscription_entities(client, non_subscribed_channels)
    # TODO: remove duplicates

    output_repository.put_many(dialogs_to_parse)
    logger.info(f'Info for {len([dialog for dialog in dialogs_to_parse if dialog])} chats saved.')
    await client.disconnect()


def start_chat_metadata_parser(
    session_backend: str,
    input_repo_spec: RepoSpec,
    output_repo_spec: RepoSpec,
    parse_subscriptions=bool,
) -> None:
    input_repository = get_repository(input_repo_spec)
    output_repository = get_repository(output_repo_spec)
    tg_client = get_telegram_client(session_type=session_backend)

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(
            chat_metadata_parser(
                input_repository,
                output_repository,
                tg_client,
                parse_subscriptions,
            ),
        )
    except KeyboardInterrupt:
        pass  # TelegramClient connection autocloses on SIGINT
    finally:
        output_repository.disconnect()


if __name__ == '__main__':
    init_logging()

    parse_subcriptions = os.getenv('PARSE_SUBSCRIPTIONS') == 'yes'
    start_chat_metadata_parser(
        session_backend=os.getenv('SESSION_DB_TYPE'),
        input_repo_spec=RepoSpec(os.getenv('json'), os.getenv('NON_SUBBED_CHANNELS_LIST')),
        output_repo_spec=RepoSpec(os.getenv('CHATS_REPO'), os.getenv('CHATS_TABLE')),
        parse_subscriptions=parse_subcriptions,
    )
