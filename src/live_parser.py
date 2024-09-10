import asyncio
import json
import logging
import os
from pathlib import Path
import sys

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.events import NewMessage

sys.path.insert(0, os.getcwd())
from utils.message_helpers import CompactMessage  # noqa: E402
from utils.repo.interface import Repository, repository_factory  # noqa: E402


def configure() -> tuple[dict[str, int], list[int]]:

    load_dotenv(dotenv_path=Path('./env/config.env'))

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s]: %(message)s'
    )

    with open(os.getenv('TG_KEYS_FILE'), 'r') as f:
        keys = json.load(f)

    with open(os.getenv('CHANNEL_LIST_FILE'), 'r', encoding='utf-16') as f:
        chats = json.load(f)
    chat_ids = list(chats.values())

    return keys, chat_ids


async def live_parser(
    keys: dict[str, int],
    chat_ids: list[int],
    repository: Repository
) -> None:

    logging.info('Initializing Telegram Client...')
    tg_client = TelegramClient(
        keys['session_name'],
        keys['api_id'],
        keys['api_hash'],
        catch_up=True
    )
    await tg_client.start()
    logging.info('Telegram Client started.')

    logging.info(f'Parsing data from {len(chat_ids)} chats...')

    @tg_client.on(NewMessage(
        chats=chat_ids,
        # commented out so that both incoming and outgoing messages are parsed
        # useful for testing: just send some message to yourself
        # incoming=True
        ))
    async def handler(event: NewMessage.Event) -> None:
        # parse only messages with text, though images may also be of interest
        if event.message.message != '':  # tbh messages with len 1 are useless
            document = CompactMessage.build_from_message(event.message)

            response = repository.put_one(document)
            logging.info(
                f'Added message {document.msg_id} '
                f'from chat "{document.chat_name}". '
                + response
            )

    await tg_client.run_until_disconnected()


def main() -> None:

    keys, chats = configure()

    repository = repository_factory(
        repo_type=os.getenv('REPOSITORY_TYPE'),
        table_name=os.getenv('TABLE_NAME'),
        collection_name=os.getenv('COLLECTION_NAME'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWD'),
        ip=os.getenv('DB_IP'),
        port=int(os.getenv('DB_PORT'))
    )
    logging.info('Connecting to database...')
    repository.connect()
    logging.info('Connection established.')

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(live_parser(keys, chats, repository))
    except KeyboardInterrupt:
        repository.disconnect()
        pass  # TelegramClient connection autocloses on SIGINT


if __name__ == '__main__':
    main()
