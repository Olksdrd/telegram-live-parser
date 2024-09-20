import asyncio
import logging
import os
import sys

from telethon import TelegramClient
from telethon.events import NewMessage

sys.path.insert(0, os.getcwd())
from configs.logging import init_logging
from parser_helpers import get_chats_to_parse, get_message_repo, get_telegram_client
from utils.message_helpers import MessageBuilder
from utils.repo.interface import Repository

logger = logging.getLogger(__name__)


async def live_parser(
    tg_client: TelegramClient, chats: list[dict], message_repository: Repository
) -> None:

    await tg_client.start()
    logger.info("Telegram Client started.")

    logger.info(f"Parsing data from {len(chats)} chats...")

    chat_ids = [chat["id"] for chat in chats]

    @tg_client.on(
        NewMessage(
            chats=chat_ids,
            # commented out so that both incoming and outgoing messages are parsed
            # useful for testing: just send some message to yourself
            # incoming=True
        )
    )
    async def handler(event: NewMessage.Event) -> None:
        # parse only messages with text, though images may also be of interest
        if event.message.message != "":  # tbh messages with len 1 are useless too
            builder = (
                MessageBuilder(event.message, chats=chats)
                .extract_text()
                .extract_dialog_name()
                .extract_forwards()
            )
            document = await builder.build()

            response = message_repository.put_one(document)
            logger.info(
                f'Added message {document["msg_id"]} '
                f'from chat {document["chat_id"]}. ' + response
            )

    await tg_client.run_until_disconnected()


def main() -> None:

    chats = get_chats_to_parse()

    message_repository = get_message_repo()

    tg_client = get_telegram_client(session_type="mongodb")

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(live_parser(tg_client, chats, message_repository))
    except KeyboardInterrupt:
        pass  # TelegramClient connection autocloses on SIGINT
    finally:
        message_repository.disconnect()


if __name__ == "__main__":
    init_logging()

    main()
