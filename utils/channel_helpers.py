from dataclasses import dataclass, field, fields
from datetime import datetime
import json
from typing import Optional, Self

from telethon import TelegramClient
from telethon.tl.types import PeerChannel, PeerChat, PeerUser, ChatFull, UserFull  # noqa: F401, E501
from telethon.functions import channels, users, messages
from telethon.errors.rpcerrorlist import ChatIdInvalidError
# from telethon.utils import get_display_name


@dataclass(frozen=True)
class CompactChannel:
    id: int
    name: str
    title: str
    description: str
    participants_count: int
    creation_date: datetime
    chats: list[int] = field(default_factory=list)  # can get into a periodic cycle if followed -> use lookup table  # noqa: E501

    @classmethod
    def build_from_api(cls: Self, response: ChatFull) -> Self:
        return CompactChannel(
            id=response.full_chat.id,
            name=response.chats[0].username,
            title=response.chats[0].title,
            description=response.full_chat.about,
            participants_count=response.full_chat.participants_count,
            creation_date=response.chats[0].date,
            chats=[chat.id for chat in response.chats[1:]]
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


@dataclass(frozen=True)
class CompactChat:
    id: int
    # name: str
    title: str
    description: str
    # participants_count: int  # 0? misleading?
    creation_date: datetime
    link: str
    parent_channel: int

    @classmethod
    def build_from_api(cls: Self, response: ChatFull) -> Self:
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


@dataclass(frozen=True)
class CompactUser:
    id: int
    username: str
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    description: Optional[str]

    @classmethod
    def build_from_api(cls: Self, response: UserFull) -> Self:
        return CompactUser(
            id=response.users[0].id,
            username=response.users[0].username,
            first_name=response.users[0].first_name,
            last_name=response.users[0].last_name,
            phone=response.users[0].phone,
            description=response.full_user.about
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


async def get_channel_info(client, id):
    try:
        return await client(channels.GetFullChannelRequest(PeerChannel(id)))
    except (ValueError, TypeError):
        print(f'Channel {id} not found.')
        return None


async def get_user_info(client, id):
    try:
        return await client(users.GetFullUserRequest(PeerUser(id)))
    except ValueError:
        print(f'User {id} not found.')
        return None


async def get_chat_info(client, id):
    try:
        return await client(messages.GetFullChatRequest(id))
    except ChatIdInvalidError:
        print(f'Chat {id} not found.')
        return None


async def amain(client, id, type='channel'):
    # print(get_display_name(PeerChannel(id)))
    if type == 'channel':
        res = await get_channel_info(client, id)
        if res is not None:
            # print(res.stringify())
            print(CompactChannel.build_from_api(res))
            pass
    elif type == 'chat':
        res = await get_chat_info(client, id)
        if res is not None:
            print(CompactChat.build_from_api(res))
    elif type == 'user':
        res = await get_user_info(client, id)
        if res is not None:
            # print(res.stringify())
            print(CompactUser.build_from_api(res))

    # get channel by username
    chat = await client.get_input_entity('username')  # to cache entity you'll use alot  # noqa: E501
    print(chat.stringify())


if __name__ == '__main__':
    with open('./tg-keys.json', 'r') as f:
        keys = json.load(f)

    client = TelegramClient('anon', keys['api_id'], keys['api_hash'])

    with client:
        client.loop.set_debug(True)
        client.loop.run_until_complete(amain(client))
        # res = client.loop.run_until_complete(amain(client))
        # print(res.stringify())
