import mongoengine
from telemongo import MongoSession


def get_telethon_session(
    user: str, passwd: str, ip: str, port: str | int, db: str
) -> MongoSession:
    MONGO_URI = f"mongodb://{user}:{passwd}@{ip}:{int(port)}/{db}?authSource=admin"

    mongoengine.connect(
        db,
        host=MONGO_URI,
    )
    session = MongoSession(db, host=MONGO_URI)

    return session
