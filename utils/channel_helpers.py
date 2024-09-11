from datetime import datetime
from typing import Optional, Self, TypedDict

from telethon import TelegramClient
from telethon.tl.types import PeerChannel, PeerChat, PeerUser, ChatFull, UserFull, TypePeer  # noqa: F401, E501
from telethon.functions import channels, users, messages
from telethon.errors.rpcerrorlist import ChatIdInvalidError


class CompactChannel(TypedDict, total=False):
    id: int
    name: str
    title: str
    description: str
    participants_count: int
    creation_date: datetime
    chats: list[int]  # can get into a periodic cycle if followed -> use lookup table  # noqa: E501

    @classmethod
    def build_from_api(cls, response: ChatFull) -> Self:
        return CompactChannel(
            id=response.full_chat.id,
            name=response.chats[0].username,
            title=response.chats[0].title,
            description=response.full_chat.about,
            participants_count=response.full_chat.participants_count,
            creation_date=response.chats[0].date,
            chats=[chat.id for chat in response.chats[1:]]
        )


class CompactChat(TypedDict, total=False):
    id: int
    # name: str
    title: str
    description: str
    # participants_count: int  # 0? misleading?
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
            parent_channel=response.chats[0].migrated_to.channel_id
        )


class CompactUser(TypedDict, total=False):
    id: int
    username: str
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
            description=response.full_user.about
        )


TypeCompact = CompactChannel | CompactChat | CompactUser


def get_peer_id(peer: TypePeer) -> int | None:
    if isinstance(peer, PeerChannel):
        return peer.channel_id
    elif isinstance(peer, PeerChat):
        return peer.chat_id
    elif isinstance(peer, PeerUser):
        return peer.user_id
    else:
        return None


async def get_channel_info(
    client: TelegramClient,
    peer: TypePeer
) -> PeerChannel:
    try:
        return await client(channels.GetFullChannelRequest(peer))
    except (ValueError, TypeError):
        print(f'{peer} not found.')
        return None


async def get_user_info(
    client: TelegramClient,
    peer: TypePeer
) -> PeerUser:
    try:
        return await client(users.GetFullUserRequest(peer))
    except ValueError:
        print(f'{peer} not found.')
        return None


async def get_chat_info(
    client: TelegramClient,
    peer: TypePeer
) -> PeerChat:
    try:
        return await client(messages.GetFullChatRequest(peer))
    except ChatIdInvalidError:
        print(f'{peer} not found.')
        return None


async def entitity_info_request(
    client: TelegramClient,
    peer: TypePeer
) -> TypeCompact:
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


# async def get_full_entity_info(peer, seen_channels):
#     peer_id = get_dialog_id(peer)
#     if peer_id not in seen_channels.keys():
#         res = await entitity_info_request(client, peer)
#         seen_channels[peer_id] = res
#     else:
#         res = seen_channels[peer_id]
#     return res
