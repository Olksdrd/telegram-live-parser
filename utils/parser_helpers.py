import os
from pathlib import Path
import json
import pytz

from telethon.tl.types import InputChannel, PeerChannel, PeerUser, PeerChat
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path('./env/config.env'))


def get_dialog_list(client, chats):

    chat_names = chats.keys()
    chat_ids = chats.items()

    chats = []
    for dialog in client.iter_dialogs():
        if (dialog.name in chat_names
                or dialog.entity.id in chat_ids):

            chats.append(InputChannel(
                dialog.entity.id,
                dialog.entity.access_hash))

    return chats


def _load_chats_dict():
    with open(os.environ.get('CHANNEL_LIST_FILE'), 'r',
              encoding='utf-16') as f:
        chats = json.load(f)

    names_dict = {val: key for key, val in chats.items()}

    return names_dict


names_dict = _load_chats_dict()


def get_chat_name(id):
    return names_dict[id]


def change_timezone(timestamp, timezone='Europe/Kyiv'):
    tz = pytz.timezone(timezone)

    return timestamp.astimezone(tz)


def get_event_id(event):
    peer_id = event.message.peer_id
    if isinstance(peer_id, PeerChannel):
        return event.message.peer_id.channel_id
    elif isinstance(peer_id, PeerUser):
        return event.message.peer_id.user_id
    elif isinstance(peer_id, PeerChat):
        return event.message.peer_id.chat_id
    else:
        raise Exception('Anonymous message?')
