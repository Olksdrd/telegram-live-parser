import os
from pathlib import Path
from datetime import datetime
import json
import pytz

from telethon import TelegramClient
from telethon.tl.types import InputChannel, PeerChannel, PeerUser, PeerChat
from telethon.events import NewMessage
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path('./env/config.env'))


def get_dialog_list(
    client: TelegramClient,
    chats: dict[str, int]
) -> list[int]:
    # no longer in use since it parsed only channels but not chats
    # TODO: further investigate this approach
    chat_names = chats.keys()
    chat_ids = chats.items()

    dialog_list = []
    for dialog in client.iter_dialogs():
        if (dialog.name in chat_names
                or dialog.entity.id in chat_ids):

            dialog_list.append(InputChannel(
                dialog.entity.id,
                dialog.entity.access_hash))

    return dialog_list


def _load_chats_dict() -> dict[int, str]:
    with open(os.getenv('CHANNEL_LIST_FILE'), 'r', encoding='utf-16') as f:
        chats = json.load(f)

    names_dict = {val: key for key, val in chats.items()}

    return names_dict


names_dict = _load_chats_dict()


def get_chat_name(chat_id: int) -> str:
    return names_dict.get(chat_id, 'Anonymous?')


def change_timezone(
    timestamp: datetime,
    timezone: str = 'Europe/Kyiv'
) -> str:
    tz = pytz.timezone(timezone)

    return timestamp.astimezone(tz)  # .isoformat()


def get_dialog_id(event: NewMessage.Event) -> int:
    peer_id = event.message.peer_id
    if isinstance(peer_id, PeerChannel):
        return peer_id.channel_id
    elif isinstance(peer_id, PeerUser):
        return peer_id.user_id
    elif isinstance(peer_id, PeerChat):
        return peer_id.chat_id
    else:
        print('Anomymous message?')
        print(event)  # never seen them before
        return -1
