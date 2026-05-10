import logging
import os

from telethon import TelegramClient

logger = logging.getLogger(__name__)


def get_telegram_client(session_type: str = 'sqlite') -> TelegramClient:
    session_name = os.getenv('SESSION_NAME')

    if session_type == 'sqlite':
        session = session_name
    elif session_type == 'mongodb':
        # NOTE: avoids installing unnecessary dependencies
        from tgparse.utils.tg_helpers import get_telemongo_session  # noqa: PLC0415

        session = get_telemongo_session(
            db=session_name,
            user=os.getenv('DB_USER'),
            passwd=os.getenv('DB_PASSWD'),
            ip=os.getenv('DB_IP'),
            port=os.getenv('DB_PORT'),
        )

    logger.info('Initializing Telegram Client...')
    return TelegramClient(
        session=session,
        api_id=os.getenv('API_ID'),
        api_hash=os.getenv('API_HASH'),
        catch_up=True,
    )
