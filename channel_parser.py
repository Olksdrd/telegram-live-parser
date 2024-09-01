import json

from telethon import TelegramClient, events

from utils.db_helpers import connect_to_mongo
from utils.chats_helpers import get_chat_name, get_event_id


def start(keys, chats):

    _, collection = connect_to_mongo()

    tg_client = TelegramClient(
        keys['session_name'],
        keys['api_id'],
        keys['api_hash'])
    tg_client.start()

    print(f'Parsing data from {len(chats)} chats.')

    @tg_client.on(events.NewMessage(chats=list(chats.values())))
    async def handler(event):
        # print(event)
        if event.message.message != '':
            chat_id = get_event_id(event)
            print(event.message.id, chat_id)
            document = {
                'Message': event.message.message,
                'Date': event.message.date,
                'Chat_Name': get_chat_name(chat_id),
                'Message_ID': event.message.id,
                }

            response = collection.insert_one(document)
            print(response)

    tg_client.run_until_disconnected()


if __name__ == '__main__':
    with open('tg-keys.json', 'r') as f:
        keys = json.load(f)

    with open('./utils/chats_to_parse.json', 'r', encoding='utf-16') as f:
        chats = json.load(f)

    start(keys, chats)
