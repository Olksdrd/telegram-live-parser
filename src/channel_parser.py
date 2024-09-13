import asyncio
import logging
import json
import os
import sys
from typing import Any

from dotenv import load_dotenv
from telethon import TelegramClient

sys.path.insert(0, os.getcwd())
from utils.channel_helpers import entitity_info_request, get_compact_name, TypeCompact  # noqa: E402, E501
from utils.message_helpers import MessageBuilder  # noqa: E402, E501
from utils.repo.interface import Repository, repository_factory  # noqa: E402, E501


def configure() -> tuple[dict[str, Any], list[dict]]:

    load_dotenv('./env/config.env')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s]: %(message)s'
    )

    with open(os.getenv('TG_KEYS_FILE'), 'r') as f:
        keys = json.load(f)

    with open(os.getenv('CHANNEL_LIST_FILE'), 'r') as f:
        chats = json.load(f)

    return keys, chats


async def get_dialog(client: TelegramClient, dialog):
    try:
        chat = await client.get_input_entity(dialog['id'])
    except ValueError:
        chat = await entitity_info_request(client, dialog)
    return chat


async def parse_channel(
    client: TelegramClient,
    repository: Repository,
    dialog: dict[TypeCompact],
) -> None:
    if not client.is_connected():
        await client.connect()

    chat = await get_dialog(client, dialog)
    if chat is None:
        logging.warning(f"Couldn't find chat {dialog['id']}. Skipping...")
        return

    logging.info(f'Retreiving data from {get_compact_name(dialog)}.')

    docs = []
    async for message in client.iter_messages(chat, limit=2):

        # don't chain them since async ones return coroutines and not builders
        builder = MessageBuilder(message, chats=[dialog]).extract_text()
        builder = builder.extract_dialog_name()
        builder = await builder.extract_engagements()
        builder = builder.extract_forwards()
        doc = await builder.build()

        docs.append(doc)
        repository.put_one(doc)

    # repository.put_many(docs)
    logging.info(f'{len(docs)} messages retreived.')


async def amain() -> None:

    keys, dialogs = configure()

    repository = repository_factory(
        repo_type=os.getenv('REPOSITORY_TYPE'),
        table_name=os.getenv('TABLE_NAME'),
        collection_name=os.getenv('COLLECTION_NAME'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWD'),
        ip=os.getenv('DB_IP'),
        port=os.getenv('DB_PORT')
    )
    repository.connect()

    logging.info('Initializing Telegram Client...')
    client = TelegramClient(
        # keys['session_name'],
        'anon',
        keys['api_id'],
        keys['api_hash']
    )
    client.loop.set_debug(True)
    await client.start()
    logging.info('Telegram Client started.')

    # not the most effective async :(
    for dialog in dialogs:
        await parse_channel(
            client,
            repository,
            dialog
        )

    repository.disconnect()


if __name__ == '__main__':
    asyncio.run(amain())
