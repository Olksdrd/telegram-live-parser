from dataclasses import dataclass, fields
from datetime import datetime
import json
import os
from pathlib import Path
from typing import Self

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.types import InputChannel
from telethon.utils import resolve_id

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


def get_chat_name(
    chat_id: int,
    # names_dict: dict[int, str]
) -> str:
    # TODO: make an adapter to allow looking in database of channels
    # adapter as a Protocol that has a get method
    # then also get chat "username"
    return names_dict.get(chat_id, None)


def get_dialog_id(message: Message) -> int:
    # just make it a method?
    return resolve_id(message.chat_id)[0]


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
    # note that chat_id + msg_id should provide unique primary key

    @classmethod
    def build_from_message(cls: Self, message: Message) -> Self:
        chat_id = get_dialog_id(message)
        return CompactMessage(
            msg_id=message.id,
            chat_id=chat_id,
            chat_name=get_chat_name(chat_id),
            msg=message.message,
            date=message.date
        )

    def __repr__(self) -> None:
        """Just a fancy multiline repr"""
        cls = self.__class__
        cls_name = cls.__name__
        indent = ' ' * 4
        res = [f'{cls_name}(']
        for f in fields(cls):
            value = getattr(self, f.name)
            res.append(f'{indent}{f.name} = {value!r},')

        res.append(')')
        return '\n'.join(res)
