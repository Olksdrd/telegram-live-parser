import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, os.getcwd())
from configs.logging import init_logging
from parser_helpers import get_channel_repo, get_telegram_client
from utils.channel_helpers import get_non_subscription_entities, get_subscriptions_list

logger = logging.getLogger(__name__)


def configure() -> list[str]:
    load_dotenv(dotenv_path=Path("./env/config.env"))

    with open(os.getenv("NON_SUBBED_CHANNELS_LIST"), "r") as f:
        non_subscribed_channels = json.load(f)

    return list(set(non_subscribed_channels))


async def amain() -> None:
    non_subscribed_channels = configure()

    repository = get_channel_repo()

    client = get_telegram_client(session_type="mongodb")

    await client.start()
    logger.info("Telegram Client started.")

    dialogs_to_parse = []
    if os.getenv("PARSE_SUBSRIPTIONS") == "yes":
        dialogs_to_parse = await get_subscriptions_list(client)

    dialogs_to_parse += await get_non_subscription_entities(
        client, non_subscribed_channels
    )

    repository.put_many(dialogs_to_parse)
    logger.info(
        f"Info for {len([dialog for dialog in dialogs_to_parse if dialog])} chats saved."
    )

    repository.disconnect()


if __name__ == "__main__":
    init_logging()

    asyncio.run(amain())
