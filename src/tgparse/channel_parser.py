import asyncio
import logging
import os
from typing import TYPE_CHECKING

from tgparse.utils.logging import init_logging
from tgparse.utils.message_helpers import MessageBuilder
from tgparse.utils.parser_helpers import (
    RepoSpec,
    get_chats_to_parse,
    get_repository,
    get_telegram_client,
)

if TYPE_CHECKING:
    from telethon import TelegramClient
    from telethon.hints import EntityLike

    from tgparse.utils.channel_helpers import TypeCompact
    from tgparse.utils.repo.interface import Repository

logger = logging.getLogger(__name__)


async def parse_channel_history(
    client: TelegramClient,
    message_repository: Repository,
    builder: MessageBuilder,
    entity: EntityLike,
) -> None:
    if not client.is_connected():
        await client.connect()

    chat = await client.get_input_entity(entity)
    if chat is None:
        logger.warning(f"Couldn't find chat {entity}. Skipping...")
        return

    logger.info(f'Retreiving data from {entity}.')

    docs = []
    async for message in client.iter_messages(chat, limit=110, wait_time=2):
        for method in builder.registered_methods:
            await method(message)

        doc = builder.build()

        docs.append(doc)
        message_repository.put_one(doc)

    # WARN: overwrites a file!
    # message_repository.put_many(docs)
    logger.info(f'{len(docs)} messages retreived.')


async def history_parser(
    chats: list[TypeCompact],
    message_repository: Repository,
    tg_client: TelegramClient,
) -> None:
    tg_client.loop.set_debug(True)
    await tg_client.connect()
    await tg_client.get_dialogs()  # NOTE: needed so that parsing by ID works
    logger.info('Telegram Client started.')

    builder = MessageBuilder(
        registered_methods=[
            'extract_text',
            'extract_dialog_info',
            'extract_engagements',
            'extract_forward_info',
        ],
        client=tg_client,
        chats=chats,
    )

    # not the most effective async :(
    for chat in chats:
        await parse_channel_history(tg_client, message_repository, builder, chat['id'])
        await asyncio.sleep(2)


def start_history_parser(
    session_backend: str,
    chats_repo_spec: RepoSpec,
    messages_repo_spec: RepoSpec,
) -> None:
    chats = get_chats_to_parse(chats_repo_spec)
    if not chats:
        logger.error('No chats to parse, exiting...')
        raise SystemExit(100)
    message_repository = get_repository(messages_repo_spec)
    tg_client = get_telegram_client(session_type=session_backend)

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(history_parser(chats, message_repository, tg_client))
    except KeyboardInterrupt:
        pass  # TelegramClient connection autocloses on SIGINT
    finally:
        message_repository.disconnect()


if __name__ == '__main__':
    init_logging()

    start_history_parser(
        session_backend=os.getenv('SESSION_DB_TYPE'),
        chats_repo_spec=RepoSpec(os.getenv('CHATS_REPO'), os.getenv('CHATS_TABLE')),
        messages_repo_spec=RepoSpec(os.getenv('MESSAGE_REPO'), os.getenv('MESSAGE_TABLE')),
    )
