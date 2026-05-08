import asyncio
import logging
import os
from typing import TYPE_CHECKING

from telethon.events import NewMessage

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

    from tgparse.utils.repo.interface import Repository

logger = logging.getLogger(__name__)


async def live_parser(
    tg_client: TelegramClient,
    chats: list[dict],
    message_repository: Repository,
) -> None:
    await tg_client.start()
    logger.info('Telegram Client started.')
    logger.info(f'Parsing data from {len(chats)} chats...')

    chat_ids = [chat['id'] for chat in chats]

    @tg_client.on(
        NewMessage(
            chats=chat_ids,
            # incoming=True,  # NOTE: for testing: just send some message to yourself
        ),
    )
    async def handler(event: NewMessage.Event) -> None:
        builder = MessageBuilder(
            registered_methods=[
                'extract_text',
                'extract_dialog_info',
                'extract_forward_info',
            ],
            client=tg_client,
            chats=chats,
        )
        # NOTE: parse only messages with text, though images may also be of interest
        if event.message.message != '':
            for method in builder.registered_methods:
                await method(event.message)
            document = builder.build()

            response = message_repository.put_one(document)
            logger.info(
                f'Added message {document["msg_id"]} from chat {document["chat_id"]}. {response}',
            )

    await tg_client.run_until_disconnected()


def start_live_parser(
    session_backend: str,
    chats_repo_spec: RepoSpec,
    messages_repo_spec: RepoSpec,
) -> None:
    chats = get_chats_to_parse(chats_repo_spec)
    message_repository = get_repository(messages_repo_spec)
    tg_client = get_telegram_client(session_type=session_backend)

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(live_parser(tg_client, chats, message_repository))
    except KeyboardInterrupt:
        pass  # TelegramClient connection autocloses on SIGINT
    finally:
        message_repository.disconnect()


if __name__ == '__main__':
    init_logging()

    start_live_parser(
        session_backend=os.getenv('SESSION_DB_TYPE'),
        chats_repo_spec=RepoSpec(os.getenv('CHATS_REPO'), os.getenv('CHATS_TABLE')),
        messages_repo_spec=RepoSpec(os.getenv('MESSAGE_REPO'), os.getenv('MESSAGE_TABLE')),
    )
