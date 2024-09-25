import logging
from datetime import datetime
from functools import singledispatch
from typing import Optional, Self, TypedDict

from telethon import TelegramClient
from telethon.errors.rpcerrorlist import (
    ChannelPrivateError,
    ChatIdInvalidError,
    UsernameInvalidError,
)
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
    User,
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


# functions to get channels/chats/users by (user)name
def cache_enitity_requests():
    cache = {}

    async def query_entity_info_by_name(
        client: TelegramClient, name: str
    ) -> TypeCompact | dict:
        if not client.is_connected():
            await client.connect()

        compact_entity = cache.get(str(name))

        if compact_entity is None:
            logger.debug(f"Request for name {str(name)}")
            entity = None
            try:
                entity = await client.get_entity(name)
            except (ValueError, UsernameInvalidError):
                logger.warning(f"Entity {name!r} not found.")
            except ChannelPrivateError:
                logger.warning(f"Either {name} is private or you have been banned.")
                entity = {"id": name, "title": "PRIVATE"}

            compact_entity = get_compact_entity(entity)
            cache[str(name)] = compact_entity

        return compact_entity

    return query_entity_info_by_name


query_entity_info_by_name = cache_enitity_requests()


async def get_non_subscription_entities(
    client: TelegramClient, non_subscribed_entities: list[str]
) -> list[TypeCompact]:
    logger.info("Adding additional entities...")

    dialogs_to_parse = []
    for entity_name in non_subscribed_entities:
        entity = await query_entity_info_by_name(client, name=entity_name)
        dialogs_to_parse.append(entity)

    return dialogs_to_parse


@singledispatch
def get_compact_entity(entity) -> dict:
    # ignore ChatForbidden and megagroups for now
    logger.warning(f"Unknown type {type(entity)}.")
    return dict()


@get_compact_entity.register
def _(entity: dict) -> dict:
    try:
        id = get_peer_id(entity["id"], add_mark=False)
        entity["id"] = id
    except AttributeError:
        pass

    return entity


@get_compact_entity.register
def _(entity: Channel) -> CompactChannel:
    compact_dialog = CompactChannel(
        id=entity.id,
        name=entity.username,
        title=entity.title,
        participants_count=entity.participants_count,
        creation_date=entity.date,
    )

    return compact_dialog


@get_compact_entity.register
def _(entity: User) -> CompactUser:
    compact_dialog = CompactUser(
        id=entity.id,
        username=entity.username,
        first_name=entity.first_name,
        last_name=entity.last_name,
    )

    return compact_dialog


@get_compact_entity.register
def _(entity: Chat) -> CompactChat:
    parent_peer = entity.migrated_to
    compact_dialog = CompactChat(
        id=entity.id,
        title=entity.title,
        creation_date=entity.date,
        parent_channel=parent_peer.channel_id if parent_peer else None,
    )

    return compact_dialog


async def get_subscriptions_list(client: TelegramClient) -> list[TypeCompact]:
    logger.info("Iterating over subscriptions list...")
    dialogs = client.iter_dialogs()

    dialogs_to_parse = []
    async for dialog in dialogs:
        compact_dialog = get_compact_entity(dialog.entity)

        if compact_dialog:
            dialogs_to_parse.append(
                {key: val for key, val in compact_dialog.items() if val is not None}
            )

    logger.info(f"{len(dialogs_to_parse)} dialogs added.")
    return dialogs_to_parse
