import json
import os
import sys
from telethon import TelegramClient

sys.path.insert(0, os.getcwd())
from utils.message_helpers import CompactMessage  # noqa: E402, E501
# from utils.reactions_helpers import MessageInteractions  # noqa: E402, E501
from utils.repo.interface import Repository, repository_factory  # noqa: E402, E501


async def amain(
    client: TelegramClient,
    repository: Repository,
    id: int
) -> None:
    chat = await client.get_input_entity(id)

    docs = []
    async for message in client.iter_messages(chat, limit=100):

        doc = CompactMessage.build_from_message(message)
        docs.append(doc)
        # repository.put_one(doc)
        # print(await MessageInteractions.build_from_message(message))

    repository.put_many(docs)

if __name__ == '__main__':
    with open('./tg-keys.json', 'r') as f:
        keys = json.load(f)

    repository = repository_factory(repo_type='cli')
    repository.connect()
    client = TelegramClient('anon', keys['api_id'], keys['api_hash'])

    with client:
        client.loop.set_debug(True)
        client.loop.run_until_complete(amain(client, repository))

    repository.disconnect()
