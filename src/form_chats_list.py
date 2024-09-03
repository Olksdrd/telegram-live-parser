import os
from pathlib import Path
import json

from dotenv import load_dotenv

from telethon import TelegramClient


def configure() -> dict[str, int]:
    load_dotenv(dotenv_path=Path("./env/config.env"))

    with open(os.getenv('TG_KEYS_FILE'), 'r') as f:
        keys = json.load(f)

    return keys


def get_all_dialogs(client: TelegramClient) -> dict[str, int]:
    return {dialog.name: dialog.entity.id
            for dialog in client.iter_dialogs()}


def main() -> None:
    keys = configure()

    client = TelegramClient(
        keys['session_name'],
        keys['api_id'],
        keys['api_hash'])
    client.start()

    chats_to_parse = get_all_dialogs(client)
    with open(os.getenv('CHANNEL_LIST_FILE'), 'w', encoding='utf=16') as f:
        json.dump(chats_to_parse, f, indent=4, ensure_ascii=False)

    print(
        f'Info for {len(chats_to_parse)} chats saved to '
        f'{os.getenv("CHANNEL_LIST_FILE")}'
    )


if __name__ == '__main__':
    main()
