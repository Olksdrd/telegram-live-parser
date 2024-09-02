import os
import sys
import logging
import json
import asyncio

from telethon import TelegramClient, events

sys.path.insert(0, os.getcwd())
import utils.db_helpers as db  # noqa: E402
import utils.parser_helpers as parser  # noqa: E402


async def start(keys, chats):

    logging.info('Connecting to database...')
    _, collection = db.connect_to_mongo()
    logging.info('Connection established.')

    logging.info('Initializing Telegram Client...')
    tg_client = TelegramClient(
        keys['session_name'],
        keys['api_id'],
        keys['api_hash'],
        catch_up=True
    )
    await tg_client.start()
    logging.info('Telegram Client started.')

    logging.info(f'Parsing data from {len(chats)} chats...')

    @tg_client.on(events.NewMessage(chats=list(chats.values())))
    async def handler(event):

        if event.message.message != '':  # parse only messages with text
            chat_id = parser.get_event_id(event)
            chat_name = parser.get_chat_name(chat_id)

            document = {
                'Message': event.message.message,
                'Date': event.message.date,
                'Chat_Name': chat_name,
                'Message_ID': event.message.id,
            }

            response = collection.insert_one(document)
            logging.info(
                f'Added message {event.message.id} '
                f'from chat "{chat_name}". '
                f'Record ID: {response.inserted_id}.'
            )

    await tg_client.run_until_disconnected()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s]: %(message)s'
    )

    with open('./tg-keys.json', 'r') as f:
        keys = json.load(f)

    with open('./utils/chats_to_parse.json', 'r', encoding='utf-16') as f:
        chats = json.load(f)

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(start(keys, chats))
    except KeyboardInterrupt:
        pass
