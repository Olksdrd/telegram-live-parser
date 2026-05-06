import datetime
import logging

import mongoengine
from mongoengine.context_managers import switch_db
from telemongo import MongoSession, UpdateState
from telethon.tl import types

logger = logging.getLogger(__name__)


class CatchupMongoSession(MongoSession):
    """
    Add integration with catch_up=True for TelegramClient,
    since the package repo seems unmaintained and out-of-date.
    """

    def __init__(self, database, **kwargs):
        super().__init__(database, **kwargs)

    def get_update_states(self):
        with switch_db(UpdateState, self.database) as _UpdateState:
            rows = list(_UpdateState._get_collection().find())

        # fmt: off
        return ((
            row["_id"],
            types.updates.State(
                pts=row["pts"],
                qts=row["qts"],
                date=datetime.datetime.fromtimestamp(row["date"], tz=datetime.UTC),
                seq=row["seq"],
                unread_count=0,
            ),
        ) for row in rows)
        # fmt: on


def get_telemongo_session(
    user: str,
    passwd: str,
    ip: str,
    port: str | int,
    db: str,
) -> MongoSession:
    mongo_uri = f'mongodb://{user}:{passwd}@{ip}:{int(port)}/{db}?authSource=admin'
    logger.info('Getting Mongo Session for Telegram Client...')
    mongoengine.connect(
        db,
        host=mongo_uri,
    )
    session = CatchupMongoSession(db, host=mongo_uri)
    logger.info('Mongo Session connected.')

    return session
