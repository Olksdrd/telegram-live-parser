import json

from telethon import TelegramClient, events
from telethon.tl.types import InputChannel


def get_dialog_list(client, chats):

    channel_names = chats.keys()
    channel_ids = chats.items()

    channels = []
    for dialog in client.iter_dialogs():
        if (dialog.name in channel_names
                or dialog.entity.id in channel_ids):

            channels.append(InputChannel(
                dialog.entity.id,
                dialog.entity.access_hash))

    return channels


def start(keys, chats):
    client = TelegramClient(
        keys['session_name'],
        keys['api_id'],
        keys['api_hash'])
    client.start()

    channels = get_dialog_list(client, chats)

    print(f'Parsing data from {len(channels)} chats.')

    @client.on(events.NewMessage(chats=channels))
    async def handler(event):
        # print(type(event.message))
        # print(type(event))
        # print(event)
        print(event.message.date, event.message.message)
        # print(type(event.message.date))  # datetime.datetime

    client.run_until_disconnected()


if __name__ == '__main__':
    with open('tg-keys.json', 'r') as f:
        keys = json.load(f)

    with open('./utils/chats_to_parse.json', 'r', encoding='utf-16') as f:
        chats = json.load(f)

    start(keys, chats)
