import json
import os
import sys

from dotenv import load_dotenv
from telethon import TelegramClient

sys.path.insert(0, os.getcwd())
from utils.channel_helpers import (
    CompactChannel,
    CompactChat,
    CompactUser,
    TypeCompact,
    entitity_info_request,
    get_peer_id,
)
from utils.repo.interface import Repository, repository_factory


async def amain(
    client: TelegramClient,
    repository: Repository,
    id: int,
    seen_channels: dict[int, TypeCompact],
) -> None:
    try:
        chat = await client.get_input_entity(id)
    except ValueError:
        chat = await entitity_info_request(client, id)
    # docs = []
    async for message in client.iter_messages(chat, limit=100):
        if message.fwd_from is not None:
            peer = message.fwd_from.from_id
            peer_id = get_peer_id(peer)
            if peer_id not in seen_channels.keys():
                res = await entitity_info_request(client, peer)
                seen_channels[peer_id] = res
            else:
                res = seen_channels[peer_id]
            if res is not None:
                # docs.append(res)
                repository.put_one(res)
    seen_channels.pop(None)  # TODO: save them somewhere?
    # repository.put_many(docs)


if __name__ == "__main__":
    with open("./tg-keys.json", "r") as f:
        keys = json.load(f)

    load_dotenv("./env/congig.env")

    repository = repository_factory(
        repo_type=os.getenv("REPOSITORY_TYPE"),
        table_name="cached_channels",
        collection_name=os.getenv("COLLECTION_NAME"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWD"),
        ip=os.getenv("DB_IP"),
        port=os.getenv("DB_PORT"),
    )
    repository.connect()

    client = TelegramClient("anon", keys["api_id"], keys["api_hash"])

    with client:
        client.loop.set_debug(True)
        client.loop.run_until_complete(amain(client, repository, seen_channels={}))

    repository.disconnect()
