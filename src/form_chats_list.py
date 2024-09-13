import os
import sys
from pathlib import Path
import json

from dotenv import load_dotenv

from telethon import TelegramClient
from telethon.tl.types import Chat

sys.path.insert(0, os.getcwd())
from utils.channel_helpers import CompactChannel, CompactChat, CompactUser  # noqa: E402, E501


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

    dialogs = client.iter_dialogs()

    dialogs_to_parse = []
    for dialog in dialogs:
        if dialog.is_channel:
            compact_dialog = CompactChannel(
                id=dialog.entity.id,
                name=dialog.entity.username,
                title=dialog.entity.title,
                participants_count=dialog.entity.participants_count,
                creation_date=dialog.entity.date,
                chats=dialog.entity.forum,
            )
        elif dialog.is_user:
            compact_dialog = CompactUser(
                id=dialog.entity.id,
                username=dialog.entity.username,
                first_name=dialog.entity.first_name,
                last_name=dialog.entity.last_name,
            )
        elif isinstance(dialog.entity, Chat):
            parent_peer = dialog.entity.migrated_to
            compact_dialog = CompactChat(
                id=dialog.entity.id,
                title=dialog.entity.title,
                creation_date=dialog.entity.date,
                parent_channel=parent_peer.channel_id if parent_peer else None
            )
        else:
            # ignore ChatForbidden and megagroups for now
            pass

        if compact_dialog:
            dialogs_to_parse.append(
                {k: v for k, v in compact_dialog.items() if v is not None})

    with open(os.getenv('CHANNEL_LIST_FILE'), 'w') as f:
        json.dump(
            obj=dialogs_to_parse,
            fp=f,
            indent=4,
            ensure_ascii=False,
            default=str
        )

    print(
        f'Info for {len(dialogs_to_parse)} chats saved to '
        f'{os.getenv("CHANNEL_LIST_FILE")}'
    )


if __name__ == '__main__':
    main()
