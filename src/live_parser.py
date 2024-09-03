import os
import sys
from pathlib import Path
import logging
import json
import asyncio

from dotenv import load_dotenv

from telethon import TelegramClient, events

sys.path.insert(0, os.getcwd())
import utils.db_helpers as db  # noqa: E402
import utils.parser_helpers as parser  # noqa: E402


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


async def start(
    keys: dict[str, int],
    chat_ids: list[int],
    collection: db.Collection
) -> None:

    logging.info('Initializing Telegram Client...')
    tg_client = TelegramClient(
        keys['session_name'],
        keys['api_id'],
        keys['api_hash'],
        catch_up=True  # does catchup even work?
    )
    await tg_client.start()
    logging.info('Telegram Client started.')

    logging.info(f'Parsing data from {len(chat_ids)} chats...')

    @tg_client.on(events.NewMessage(
        chats=chat_ids,
        # commented out so that both incoming and outgoing messages are parsed
        # useful for testing: just send some message to yourself
        # incoming=True
        ))
    async def handler(event):
        # parse only messages with text, though images may also be of interest
        if event.message.message != '':  # tbh messages with len 1 are useless
            chat_id = parser.get_dialog_id(event)
            chat_name = parser.get_chat_name(chat_id)

            document = {
                'Message': event.message.message,
                'Date': parser.change_timezone(event.message.date),
                'Chat_Name': chat_name,
                'Message_ID': event.message.id,
                # TODO: investigate other attributes in more details
            }
            # note that chat_id + Message_ID should provide unique primary key

            response = collection.insert_one(document)
            logging.info(
                f'Added message {event.message.id} '
                f'from chat "{chat_name}". '
                f'Record ID: {response.inserted_id}.'
            )

    await tg_client.run_until_disconnected()


def main() -> None:

    keys, chats = configure()

    logging.info('Connecting to database...')
    db_client, collection = db.connect_to_mongo()
    logging.info('Connection established.')

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(start(keys, chats, collection))
    except KeyboardInterrupt:
        db_client.close()
        pass  # TelegramClient connection autocloses on SIGINT


if __name__ == '__main__':
    main()
