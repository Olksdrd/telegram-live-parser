import asyncio
import logging
import os

from telethon.events import NewMessage
from typing import TYPE_CHECKING

from utils.logging import init_logging
from utils.parser_helpers import get_chats_to_parse, get_message_repo, get_telegram_client
from utils.message_helpers import MessageBuilder

if TYPE_CHECKING:
    from telethon import TelegramClient

    from utils.repo.interface import Repository

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
        # parse only messages with text, though images may also be of interest
        builder = MessageBuilder(registered_methods=[], client=tg_client, chats=chats)
        if event.message.message != '':  # tbh messages with len 1 are useless too
            await builder.extract_text(event.message)
            await builder.extract_dialog_info(event.message)
            await builder.extract_forward_info(event.message)
            document = builder.build()

            response = message_repository.put_one(document)
            logger.info(
                f'Added message {document["msg_id"]} from chat {document["chat_id"]}. ' + response,
            )

    await tg_client.run_until_disconnected()


def main() -> None:
    chats = get_chats_to_parse()

    message_repository = get_message_repo()

    tg_client = get_telegram_client(session_type=os.getenv('SESSION_DB_TYPE'))

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(live_parser(tg_client, chats, message_repository))
    except KeyboardInterrupt:
        pass  # TelegramClient connection autocloses on SIGINT
    finally:
        message_repository.disconnect()


if __name__ == '__main__':
    init_logging()

    main()
