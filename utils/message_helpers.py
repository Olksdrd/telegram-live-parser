from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Self, TypedDict

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.custom.message import Message
from telethon.utils import resolve_id
from telethon.tl.types import MessageReactions, ReactionCount, ReactionEmoji, ReactionCustomEmoji, MessageReplies  # noqa: E501
from telethon.tl.types import Document, DocumentAttributeCustomEmoji
from telethon import functions

sys.path.insert(0, os.getcwd())
from utils.channel_helpers import get_peer_id  # noqa: E402

load_dotenv(dotenv_path=Path('./env/config.env'))


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


# TODO: cache requests
async def get_document_info(client: TelegramClient, document_id: int) -> Document:  # noqa: E501
    document = await client(functions.messages.GetCustomEmojiDocumentsRequest(
        document_id=[document_id]
    ))
    return document[0]


async def get_custom_emoji_alt(document: Document) -> str:
    for attribute in document.attributes:
        if isinstance(attribute, DocumentAttributeCustomEmoji):
            return attribute.alt


async def get_reaction_type(reaction_obj: ReactionCount) -> str:
    if isinstance(reaction_obj.reaction, ReactionEmoji):
        return reaction_obj.reaction.emoticon
    elif isinstance(reaction_obj.reaction, ReactionCustomEmoji):
        return str(reaction_obj.reaction.document_id)


async def unwrap_reactions(msg_reactions: MessageReactions | None) -> dict[str, int]:  # noqa: E501
    reactions = {}
    if msg_reactions is None:
        return reactions
    for reaction_obj in msg_reactions.results:
        reaction_type = await get_reaction_type(reaction_obj)
        reactions[reaction_type] = reaction_obj.count

    return reactions


async def get_reply_count(replies_obj: MessageReplies | None) -> int:
    if replies_obj is None:
        # print('None replies')
        return 0
    else:
        return replies_obj.replies


class CompactMessage(TypedDict, total=False):
    """
    More compact representation of a message.
    Only stores the attributes we actually need.
    """
    msg_id: int
    chat_id: int
    msg: str
    date: datetime
    chat_name: str
    chat_title: str
    views: int
    forwards: int
    replies: int
    reactions: dict[str, int]
    fwd_from: int
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


class MessageBuilder:
    def __init__(self, new_msg) -> None:
        self.new_msg = new_msg
        self.message = CompactMessage()

    def extract_text(self) -> Self:
        self.message['msg_id'] = self.new_msg.id
        self.message['chat_id'] = get_dialog_id(self.new_msg)
        self.message['msg'] = self.new_msg.message
        self.message['date'] = self.new_msg.date
        return self

    async def extract_engagements(self) -> Self:
        self.message['views'] = self.new_msg.views
        self.message['forwards'] = self.new_msg.forwards
        self.message['replies'] = await get_reply_count(self.new_msg.replies)
        self.message['reactions'] = await unwrap_reactions(self.new_msg.reactions)  # noqa: E501
        return self

    def extract_forwards(self) -> Self:
        forwarded_from_peer = self.new_msg.fwd_from
        if forwarded_from_peer is not None:
            peer_id = get_peer_id(forwarded_from_peer.from_id)
            if peer_id is not None:
                self.message['fwd_from'] = peer_id
        return self

    async def build(self):
        return self.message
