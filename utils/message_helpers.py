from datetime import datetime
import os
from pathlib import Path
import sys
from typing import Self, TypedDict, Coroutine, Optional

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


class MessageBuilder:
    def __init__(
        self,
        new_msg: Message,
        chats: Optional[list[dict]] = None
    ) -> None:
        self.new_msg = new_msg
        self.message = CompactMessage()
        if chats:
            self.chats = {chat['id']: chat for chat in chats}

    def extract_text(self) -> Self:
        self.message['msg_id'] = self.new_msg.id
        self.message['chat_id'] = get_dialog_id(self.new_msg)
        self.message['msg'] = self.new_msg.message
        self.message['date'] = self.new_msg.date
        return self

    def extract_dialog_name(self) -> Self:
        chat_name = self.chats[self.message['chat_id']].get('name')
        chat_title = self.chats[self.message['chat_id']].get('title')
        if chat_name is None:
            chat_name = self.chats[self.message['chat_id']].get('username')
        self.message['chat_name'] = chat_name
        self.message['chat_title'] = chat_title
        return self

    async def extract_engagements(self) -> Coroutine:
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

    async def build(self) -> Coroutine:
        return self.message
