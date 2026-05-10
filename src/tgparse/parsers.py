import asyncio
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from telethon.events import NewMessage

from tgparse.utils.channel_helpers import (
    get_non_subscription_entities,
    get_subscriptions_list,
)
from tgparse.utils.message_helpers import MessageBuilder
from tgparse.utils.parser_helpers import (
    get_telegram_client,
)
from tgparse.utils.repo.interface import (
    RepoSpec,
    get_chats_to_parse,
    get_repository,
)

if TYPE_CHECKING:
    from telethon import TelegramClient
    from telethon.hints import EntityLike

    from tgparse.utils.channel_helpers import TypeCompact
    from tgparse.utils.repo.interface import Repository


logger = logging.getLogger(__name__)


async def parse_channel_history(
    tg_client: TelegramClient,
    message_repository: Repository,
    builder: MessageBuilder,
    entity: EntityLike,
) -> None:
    if not tg_client.is_connected():
        await tg_client.connect()

    chat = await tg_client.get_input_entity(entity)
    if chat is None:
        logger.warning(f"Couldn't find chat {entity}. Skipping...")
        return

    logger.info(f'Retreiving data from {entity}.')

    docs = []
    async for message in tg_client.iter_messages(chat, limit=110, wait_time=2):
        for method in builder.registered_methods:
            await method(message)

        doc = builder.build()

        docs.append(doc)
        message_repository.put_one(doc)

    # WARN: overwrites a file!
    # message_repository.put_many(docs)
    logger.info(f'{len(docs)} messages retreived.')


async def history_parser(
    tg_client: TelegramClient,
    chats: list[TypeCompact],
    message_repository: Repository,
    **kwargs,
) -> None:
    tg_client.loop.set_debug(True)
    await tg_client.connect()
    await tg_client.get_dialogs()  # NOTE: needed so that parsing by ID works
    logger.info('Telegram Client started.')

    builder = MessageBuilder(
        registered_methods=[
            'extract_text',
            'extract_dialog_info',
            'extract_engagements',
            'extract_forward_info',
        ],
        client=tg_client,
        chats=chats,
    )

    # not the most effective async :(
    for chat in chats:
        await parse_channel_history(tg_client, message_repository, builder, chat['id'])
        await asyncio.sleep(2)


async def chat_metadata_parser(
    tg_client: TelegramClient,
    non_subscribed_channels: list[str],
    output_repository: Repository,
    parse_subscriptions: bool,
) -> None:
    await tg_client.start()
    logger.info('Telegram Client started.')

    dialogs_to_parse = []
    if parse_subscriptions:
        dialogs_to_parse = await get_subscriptions_list(tg_client)

    dialogs_to_parse += await get_non_subscription_entities(tg_client, non_subscribed_channels)
    # TODO: remove duplicates

    output_repository.put_many(dialogs_to_parse)
    logger.info(f'Info for {len([dialog for dialog in dialogs_to_parse if dialog])} chats saved.')
    await tg_client.disconnect()


async def live_parser(
    tg_client: TelegramClient,
    chats: list[dict],
    message_repository: Repository,
    **kwargs,
) -> None:
    await tg_client.start()
    logger.info('Telegram Client started.')
    logger.info(f'Parsing data from {len(chats)} chat(s)...')

    chat_ids = [chat['id'] for chat in chats]

    @tg_client.on(
        NewMessage(
            chats=chat_ids,
            # incoming=True,  # NOTE: for testing: just send some message to yourself
        ),
    )
    async def handler(event: NewMessage.Event) -> None:
        builder = MessageBuilder(
            registered_methods=[
                'extract_text',
                'extract_dialog_info',
                'extract_forward_info',
            ],
            client=tg_client,
            chats=chats,
        )
        # NOTE: parse only messages with text, though images may also be of interest
        if event.message.message != '':
            for method in builder.registered_methods:
                await method(event.message)
            document = builder.build()

            response = message_repository.put_one(document)
            logger.info(
                f'Added message {document["msg_id"]} from chat {document["chat_id"]}. {response}',
            )

    await tg_client.run_until_disconnected()


def start_parser(
    parser: Callable,
    session_backend: str,
    input_repo_spec: RepoSpec,
    output_repo_spec: RepoSpec,
    parse_subscriptions: bool = False,
) -> None:
    chats = get_chats_to_parse(input_repo_spec)
    if not (chats or parse_subscriptions):
        logger.error('No chats to parse, exiting...')
        raise SystemExit(100)
    output_repository = get_repository(output_repo_spec)
    tg_client = get_telegram_client(session_type=session_backend)

    # handle SIGINT without an error message from asyncio
    try:
        asyncio.run(
            parser(
                tg_client,
                chats,
                output_repository,
                parse_subscriptions=parse_subscriptions,
            ),
        )
    except KeyboardInterrupt:
        pass  # TelegramClient connection autocloses on SIGINT
    finally:
        output_repository.disconnect()
