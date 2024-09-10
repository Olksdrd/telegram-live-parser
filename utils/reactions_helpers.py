from dataclasses import dataclass, field
from typing import Self

from telethon import TelegramClient
from telethon.tl.custom.message import Message
from telethon.tl.types import MessageReactions, ReactionCount, ReactionEmoji, ReactionCustomEmoji, MessageReplies  # noqa: E501
from telethon.tl.types import Document, DocumentAttributeCustomEmoji
from telethon import functions

from utils.compact import Compact


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
        print('None replies')
        return 0
    else:
        return replies_obj.replies


@dataclass(frozen=True, repr=False)
class MessageInteractions(Compact):
    views: int
    forwards: int
    replies: int
    reactions: dict[str, int] = field(default_factory=dict)

    @classmethod
    async def build_from_message(cls: Self, message: Message) -> Self:
        return MessageInteractions(
            views=message.views,
            forwards=message.forwards,
            replies=await get_reply_count(message.replies),
            reactions=await unwrap_reactions(message.reactions)
        )

    # def __repr__(self) -> None:
    #     return super().__repr__()
