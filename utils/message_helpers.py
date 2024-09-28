import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Self, TypedDict

from dotenv import load_dotenv
from telethon import TelegramClient, functions
from telethon.tl.custom.message import Message
from telethon.tl.types import (
    Document,
    MessageReactions,
    MessageReplies,
    ReactionCount,
    MessageFwdHeader,
)
from telethon.utils import resolve_id

sys.path.insert(0, os.getcwd())
from utils.channel_helpers import get_compact_name, query_entity_info

load_dotenv(dotenv_path=Path("./env/config.env"))

logger = logging.getLogger(__name__)


def get_dialog_id(message: Message) -> int:
    """Return unmarked id of a chat where message came from"""
    return resolve_id(message.chat_id)[0]


async def query_document_info(client: TelegramClient, document_id: int) -> Document:
    """
    Send a (rather slow) request to Telegram to get more info about custom emoji.
    Only small fraction of channels uses them.
    """
    document = await client(
        functions.messages.GetCustomEmojiDocumentsRequest(document_id=[document_id])
    )
    return document[0]


def extract_custom_emoji_alt(document: Document) -> str:
    """
    Extract alternative representation of a custom emoji in UTF-8/16.
    Note that it not always correctly represents the meaining of a custom emoji,
    but usually it's close enough.
    """
    for attribute in document.attributes:
        if hasattr(attribute, "alt"):
            return attribute.alt


def cache_custom_emoji_requests() -> Callable[[TelegramClient, int], str]:
    """
    Since requests are slow and channels usually use only a couple of custom emojis,
    which are repeated in every message, caching drastically reduces the number of
    DocumentRequests we're making.

    functools.lru_cache is not suitable, since we don't want to cache a client too,
    and cachetools is not in standard library -> easier to just use a dictionary.
    """
    cache: dict[int, str] = {}

    async def get_custom_emoji_alt(client: TelegramClient, document_id: int) -> str:
        alt = cache.get(document_id)
        if alt is None:
            logger.debug(f"Sending request for custom emoji {document_id}...")
            doc = await query_document_info(client, document_id)
            alt = extract_custom_emoji_alt(doc)
            cache[document_id] = alt
        return alt

    return get_custom_emoji_alt


get_custom_emoji_alt = cache_custom_emoji_requests()


async def get_reaction_type(client: TelegramClient, reaction_obj: ReactionCount) -> str:
    """
    There are two distinct type of reactions in Telegram:
    - ordinary utf-8/16 emoticons
    - custom png/webp reactions, enabled on some channels

    Custom ones are marked by * to prevent collisions with ordinary emoticons.
    """
    try:
        return reaction_obj.reaction.emoticon
    except AttributeError:
        custom_reaction_id = reaction_obj.reaction.document_id
        reaction = await get_custom_emoji_alt(client, custom_reaction_id)
        return f"*{reaction}"


async def unwrap_reactions(
    msg_reactions: MessageReactions | None, client: TelegramClient | None = None
) -> dict[str, int]:
    """
    Return all reactions to a message with counts
    Ex: {'😁': 23, '👍': 12, '❤': 2}
    Note that it's pointless to use it on recent messages
    """
    reactions: dict[str, int] = {}
    if msg_reactions is None:
        return reactions
    for reaction_obj in msg_reactions.results:
        reaction_type = await get_reaction_type(client, reaction_obj)
        reactions[reaction_type] = reaction_obj.count

    return reactions


def get_reply_count(replies_obj: MessageReplies | None) -> int:
    if replies_obj is None:
        return 0
    return replies_obj.replies


async def get_fwd_from_info(
    client: TelegramClient, from_peer: MessageFwdHeader
) -> dict[str, Any]:
    if from_peer.from_id is not None:
        fwd_peer_info = await query_entity_info(client, from_peer.from_id)
    elif from_peer.from_name is not None:
        fwd_peer_info = {"full_name": from_peer.from_name}
    else:
        fwd_peer_info = {}
    return fwd_peer_info


class CompactMessage(TypedDict, total=False):
    """
    More compact representation of a message.
    Only stores the attributes we actually need.
    """

    msg: str
    date: datetime
    msg_id: int
    chat_id: int
    chat_name: str
    chat_title: str
    views: int
    forwards: int
    replies: int
    reactions: dict[str, int]
    fwd_from: dict[str, Any]
    # note that chat_id + msg_id should provide unique primary key


class MessageBuilder:
    def __init__(
        self,
        registered_methods: list[str],
        client: TelegramClient | None = None,
        chats: list[dict] | None = None,
    ) -> None:
        self._msg = CompactMessage()
        self.registered_methods = [
            getattr(self, method) for method in registered_methods
        ]
        self.client = client
        if chats:
            self.chats = {chat["id"]: chat for chat in chats}

    def reset(self) -> None:
        self._msg = CompactMessage()

    async def extract_text(self, new_msg: Message) -> Self:
        self._msg["msg"] = new_msg.message
        self._msg["date"] = new_msg.date
        return self

    async def extract_dialog_info(self, new_msg: Message) -> Self:
        self._msg["msg_id"] = new_msg.id

        dialog_id = get_dialog_id(new_msg)
        self._msg["chat_id"] = dialog_id

        chat_name = get_compact_name(self.chats.get(dialog_id))
        self._msg["chat_name"] = chat_name

        chat_title = self.chats.get(dialog_id).get("title")
        self._msg["chat_title"] = chat_title
        return self

    async def extract_engagements(self, new_msg: Message) -> Self:
        self._msg["views"] = new_msg.views
        self._msg["forwards"] = new_msg.forwards
        self._msg["replies"] = get_reply_count(new_msg.replies)
        self._msg["reactions"] = await unwrap_reactions(
            msg_reactions=new_msg.reactions, client=self.client
        )
        return self

    async def extract_forward_info(self, new_msg: Message) -> Self:
        forwarded_from_peer = new_msg.fwd_from
        if forwarded_from_peer is not None:
            fwd_peer_info = await get_fwd_from_info(self.client, forwarded_from_peer)
            self._msg["fwd_from"] = {
                str(key): val for key, val in fwd_peer_info.items() if val is not None
            }
        return self

    def build(self) -> CompactMessage:
        final_msg = self._msg
        self.reset()
        return final_msg
