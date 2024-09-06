import os
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Self
import json
import pytz

from telethon import TelegramClient
from telethon.tl.types import InputChannel
from telethon.events import NewMessage
from telethon.utils import resolve_id
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path('./env/config.env'))


def get_dialog_list(
    client: TelegramClient,
    chats: dict[str, int]
) -> list[int]:
    # ! no longer in use since it parsed only channels but not chats
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


def get_chat_name(chat_id: int) -> str:  # TODO add all dependencies
    return names_dict.get(chat_id, 'Anonymous?')


def change_timezone(
    timestamp: datetime,
    timezone: str = 'Europe/Kyiv'
) -> datetime:  # str
    tz = pytz.timezone(timezone)

    # return isoformat str for DynamoDB
    return timestamp.astimezone(tz)  # .isoformat()


def get_dialog_id(event: NewMessage.Event) -> int:
    return resolve_id(event.message.chat_id)[0]


@dataclass(frozen=True)
class CompactMessage:
    """
    More compact representation of a message.
    Only stores the attributes we actually need.
    """
    msg_id: int
    chat_id: int
    chat_name: str
    msg: str
    date: datetime
    # TODO: investigate other attributes in more details
    # forward: Optional[Chat] or just id
    # note that chat_id + msg_id should provide unique primary key

    @classmethod
    def build_from_event(cls: Self, event: NewMessage.Event) -> Self:
        chat_id = get_dialog_id(event)
        return CompactMessage(
            msg_id=event.message.id,
            chat_id=chat_id,
            chat_name=get_chat_name(chat_id),
            msg=event.message.message,
            date=event.message.date
        )
