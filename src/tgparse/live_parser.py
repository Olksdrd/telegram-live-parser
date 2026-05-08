import asyncio
import logging
import os
from typing import TYPE_CHECKING

from telethon.events import NewMessage

from tgparse.utils.logging import init_logging
from tgparse.utils.message_helpers import MessageBuilder
from tgparse.utils.parser_helpers import (
    get_chats_to_parse,
    get_message_repository,
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
            # useful for testing: just send some message to yourself
            # incoming=True,
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
        # parse only messages with text, though images may also be of interest
        if event.message.message != '':
            for method in builder.registered_methods:
                await method(event.message)
            document = builder.build()

            response = message_repository.put_one(document)
            logger.info(
                f'Added message {document["msg_id"]} from chat {document["chat_id"]}. ' + response,
            )

    await tg_client.run_until_disconnected()


def start_live_parser(
    session_backend: str,
    chats_repository: str,
    chats_path: str,
    message_repository: str,
    output_path: str,
) -> None:
    chats = get_chats_to_parse(repo_type=chats_repository, table_name=chats_path)
    message_repository = get_message_repository(
        repo_type=message_repository,
        table_name=output_path,
    )
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
        chats_repository=os.getenv('CHATS_REPO'),
        chats_path=os.getenv('CHATS_TABLE'),
        message_repository=os.getenv('MESSAGE_REPO'),
        output_path=os.getenv('MESSAGE_TABLE'),
    )
