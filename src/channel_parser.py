import json
import os
import sys

from dotenv import load_dotenv
from telethon import TelegramClient

sys.path.insert(0, os.getcwd())
from utils.message_helpers import MessageBuilder  # noqa: E402, E501
from utils.repo.interface import Repository, repository_factory  # noqa: E402, E501


async def amain(
    client: TelegramClient,
    repository: Repository,
    id: int
) -> None:
    chat = await client.get_input_entity(id)

    docs = []
    async for message in client.iter_messages(chat, limit=100):

        # don't chain them since async ones return coroutines and not builders
        builder = MessageBuilder(message).extract_text()
        builder = await builder.extract_engagements()
        builder = builder.extract_forwards()
        doc = await builder.build()

        docs.append(doc)
        repository.put_one(doc)

    # repository.put_many(docs)

if __name__ == '__main__':
    with open('./tg-keys.json', 'r') as f:
        keys = json.load(f)

    load_dotenv('./env/congig.env')

    repository = repository_factory(
        repo_type=os.getenv('REPOSITORY_TYPE'),
        table_name=os.getenv('TABLE_NAME'),
        collection_name=os.getenv('COLLECTION_NAME'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWD'),
        ip=os.getenv('DB_IP'),
        port=int(os.getenv('DB_PORT'))
    )
    repository.connect()

    client = TelegramClient('anon', keys['api_id'], keys['api_hash'])

    with client:
        client.loop.set_debug(True)
        client.loop.run_until_complete(amain(
            client,
            repository,
            id=-1
        ))

    repository.disconnect()
