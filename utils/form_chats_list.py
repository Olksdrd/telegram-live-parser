import json

from telethon import TelegramClient


def form_channels_lists(client):
    chats_to_parse = {}
    for dialog in client.iter_dialogs():
        chats_to_parse[dialog.name] = dialog.entity.id
        # print(dialog.name, dialog.entity.id)

    return chats_to_parse


def main(keys):
    client = TelegramClient(
        keys['session_name'],
        keys['api_id'],
        keys['api_hash'])
    client.start()

    chats_to_parse = form_channels_lists(client)
    # print(list(zip(channel_names, channel_ids))[:5])
    with open('./utils/chats_to_parse.json', 'w', encoding='utf=16') as f:
        json.dump(chats_to_parse, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    with open('tg-keys.json', 'r') as f:
        keys = json.load(f)

    main(keys)
