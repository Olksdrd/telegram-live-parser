from datetime import datetime
from typing import Optional, Self, TypedDict

from telethon import TelegramClient
from telethon.errors.rpcerrorlist import ChatIdInvalidError
from telethon.functions import channels, messages, users
from telethon.tl.types import PeerChannel, PeerChat, PeerUser, TypePeer
from telethon.tl.types.messages import ChatFull
from telethon.tl.types.users import UserFull


class CompactChannel(TypedDict, total=False):
    id: int
    name: str
    title: str
    description: str
    participants_count: int
    creation_date: datetime
    chats: list[int]  # can get into a periodic cycle if followed -> use lookup table

    @classmethod
    def build_from_api(cls, response: ChatFull) -> Self:
        return CompactChannel(
            id=response.full_chat.id,
            name=response.chats[0].username,
            title=response.chats[0].title,
            description=response.full_chat.about,
            participants_count=response.full_chat.participants_count,
            creation_date=response.chats[0].date,
            chats=[chat.id for chat in response.chats[1:]],
        )


class CompactChat(TypedDict, total=False):
    id: int
    # name: str
    title: str
    description: str
    # participants_count: int  # always 0?
    creation_date: datetime
    link: str
    parent_channel: int

    @classmethod
    def build_from_api(cls, response: ChatFull) -> Self:
        return CompactChat(
            id=response.full_chat.id,
            # name=response.chats[0].username,
            title=response.chats[0].title,
            description=response.full_chat.about,
            # participants_count=response.chats[0].participants_count,
            creation_date=response.chats[0].date,
            link=response.full_chat.exported_invite.link,
            parent_channel=response.chats[0].migrated_to.channel_id,
        )


class CompactUser(TypedDict, total=False):
    id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    description: Optional[str]

    @classmethod
    def build_from_api(cls, response: UserFull) -> Self:
        return CompactUser(
            id=response.users[0].id,
            username=response.users[0].username,
            first_name=response.users[0].first_name,
            last_name=response.users[0].last_name,
            phone=response.users[0].phone,
            description=response.full_user.about,
        )


TypeCompact = CompactChannel | CompactChat | CompactUser


def get_compact_name(dialog: TypeCompact) -> str | None:
    """Just get some recognizable name to display in logs instead of id"""
    name = dialog.get("title")
    if name is None:
        name = dialog.get("username")
    return name


def get_peer_id(peer: TypePeer) -> int | None:
    """Why haven't they just called the attribute 'id'?"""
    if hasattr(peer, "channel_id"):
        return peer.channel_id
    elif hasattr(peer, "chat_id"):
        return peer.chat_id
    elif hasattr(peer, "user_id"):
        return peer.user_id
    else:
        # TODO: handle it more nicely outside a function
        print(f"Unknown peer type {type(peer)}: {peer}")
        return None


# These 3 functions just send a request to a server to get *all* the info about Channel/Chat/User
# These requests are slow, so it's better to cache results or use lookup table first
async def get_channel_info(client: TelegramClient, peer: TypePeer) -> ChatFull | None:
    try:
        return await client(channels.GetFullChannelRequest(peer))
    except (ValueError, TypeError):
        print(f"{peer} not found.")
        return None


async def get_user_info(client: TelegramClient, peer: TypePeer) -> UserFull | None:
    try:
        return await client(users.GetFullUserRequest(peer))
    except ValueError:
        print(f"{peer} not found.")
        return None


async def get_chat_info(client: TelegramClient, peer: TypePeer) -> ChatFull | None:
    try:
        return await client(messages.GetFullChatRequest(peer))
    except ChatIdInvalidError:
        print(f"{peer} not found.")
        return None


async def entitity_info_request(client: TelegramClient, peer: TypePeer) -> TypeCompact:
    if isinstance(peer, PeerChannel):
        res = await get_channel_info(client, peer)
        if res is not None:
            return CompactChannel.build_from_api(res)
    elif isinstance(peer, PeerChat):
        res = await get_chat_info(client, peer)
        if res is not None:
            return CompactChat.build_from_api(res)
    elif isinstance(peer, PeerUser):
        res = await get_user_info(client, peer)
        if res is not None:
            return CompactUser.build_from_api(res)
