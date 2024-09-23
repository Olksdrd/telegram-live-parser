import logging
from datetime import datetime
from typing import Optional, Self, TypedDict

from telethon import TelegramClient
from telethon.errors.rpcerrorlist import ChannelPrivateError, ChatIdInvalidError
from telethon.functions import channels, messages, users
from telethon.tl.types import (
    Channel,
    Chat,
    MessageFwdHeader,
    PeerChannel,
    PeerChat,
    PeerUser,
    TypeInputPeer,
    TypePeer,
)
from telethon.tl.types.messages import ChatFull
from telethon.tl.types.users import UserFull
from telethon.utils import get_peer_id

logger = logging.getLogger(__name__)


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
    name = dialog.get("name")
    if name is None:
        name = dialog.get("username")
    return name


def get_forward_id(fwd_header: MessageFwdHeader) -> int | None:
    """
    Extract id of a peer from which the message was forwaded.

    Sometimes ".from_id" is None, but there is info about user's name in ".from_name" attribute.
    It's not clear what can be done with it further, so it's skipped for now.
    """
    peer = fwd_header.from_id
    try:
        return get_peer_id(peer, add_mark=False)
    except TypeError:
        logger.warning(f"No peer info. Forwarded from {fwd_header.from_name}")
        return None


# These 3 functions just send a request to a server to get *all* the info about Channel/Chat/User
# These requests are slow, so it's better to cache results or use lookup table first
async def get_channel_info(client: TelegramClient, peer: TypePeer) -> ChatFull | None:
    try:
        return await client(channels.GetFullChannelRequest(peer))
    except (ValueError, TypeError):
        logger.warning(f"{peer} not found.")
        return None
    except ChannelPrivateError:
        logger.warning(f"{peer} is private.")
        return None


async def get_user_info(client: TelegramClient, peer: TypePeer) -> UserFull | None:
    try:
        return await client(users.GetFullUserRequest(peer))
    except ValueError:
        logger.warning(f"{peer} not found.")
        return None


async def get_chat_info(client: TelegramClient, peer: TypePeer) -> ChatFull | None:
    try:
        return await client(messages.GetFullChatRequest(peer))
    except ChatIdInvalidError:
        logger.warning(f"{peer} not found.")
        return None


async def peer_info_request(
    client: TelegramClient, peer: TypePeer
) -> TypeCompact | None:
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


async def get_peer_by_id(
    client: TelegramClient, dialog: TypeCompact
) -> TypeCompact | TypeInputPeer | None:
    try:
        chat = await client.get_input_entity(dialog["id"])
    except ValueError:
        chat = await peer_info_request(client, dialog)
    return chat


async def get_channel_info_by_name(
    client: TelegramClient, name: str
) -> CompactChannel | None:
    if not client.is_connected():
        await client.connect()

    try:
        channel: Channel = await client.get_entity(name)
        return CompactChannel(
            id=channel.id,
            name=channel.username,
            title=channel.title,
            participants_count=channel.participants_count,
            creation_date=channel.date,
        )
    except ValueError:
        logger.warning(f"Channel '{name}' not found.")


async def get_non_subscription_channels(
    client: TelegramClient, non_subscribed_channels: list[str]
) -> list[TypeCompact]:
    logger.info("Adding additional public channels...")

    dialogs_to_parse = []
    for channel_name in non_subscribed_channels:
        channel = await get_channel_info_by_name(client, name=channel_name)
        dialogs_to_parse.append(channel)

    return dialogs_to_parse


async def get_subscriptions_list(client: TelegramClient) -> list[TypeCompact]:
    logger.info("Iterating over subscriptions list...")
    dialogs = client.iter_dialogs()

    dialogs_to_parse = []
    async for dialog in dialogs:
        if dialog.is_channel:
            compact_dialog = CompactChannel(
                id=dialog.entity.id,
                name=dialog.entity.username,
                title=dialog.entity.title,
                participants_count=dialog.entity.participants_count,
                creation_date=dialog.entity.date,
            )
        elif dialog.is_user:
            compact_dialog = CompactUser(
                id=dialog.entity.id,
                username=dialog.entity.username,
                first_name=dialog.entity.first_name,
                last_name=dialog.entity.last_name,
            )
        elif isinstance(dialog.entity, Chat):
            parent_peer = dialog.entity.migrated_to
            compact_dialog = CompactChat(
                id=dialog.entity.id,
                title=dialog.entity.title,
                creation_date=dialog.entity.date,
                parent_channel=parent_peer.channel_id if parent_peer else None,
            )
        else:
            # ignore ChatForbidden and megagroups for now
            pass

        if compact_dialog:
            dialogs_to_parse.append(
                {key: val for key, val in compact_dialog.items() if val is not None}
            )

    logger.info(f"{len(dialogs_to_parse)} dialogs added.")
    return dialogs_to_parse
