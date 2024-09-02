import os
from pathlib import Path
import json

from dotenv import load_dotenv

from telethon import TelegramClient


def get_chats_dict(client):
    return {dialog.name: dialog.entity.id
            for dialog in client.iter_dialogs()}


def main(keys):
    client = TelegramClient(
        keys['session_name'],
        keys['api_id'],
        keys['api_hash'])
    client.start()

    chats_to_parse = get_chats_dict(client)
    with open(os.environ.get('CHANNEL_LIST_FILE'), 'w',
              encoding='utf=16') as f:
        json.dump(chats_to_parse, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    load_dotenv(dotenv_path=Path("./env/config.env"))

    with open(os.environ.get('TG_KEYS_FILE'), 'r') as f:
        keys = json.load(f)

    main(keys)
