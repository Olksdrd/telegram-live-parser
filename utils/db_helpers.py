import os
from pathlib import Path

from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path('./env/config.env'))


def get_mongo_client(
    user: str, passwd: str, ip: str, port: str
) -> MongoClient:
    db_uri = f'mongodb://{user}:{passwd}@{ip}:{port}'
    return MongoClient(db_uri)


def get_collection(
    client: MongoClient,
    table_name: str,
    collection_name: str
) -> Collection:
    db = client.get_database(table_name)
    return db.get_collection(collection_name)


def connect_to_mongo() -> tuple[MongoClient, Collection]:
    mongo_client = get_mongo_client(
        user=str(os.getenv('DB_USER')),
        passwd=str(os.getenv('DB_PASSWD')),
        ip=os.getenv('DB_IP'),
        port=os.getenv('DB_PORT')
    )

    collection = get_collection(
        client=mongo_client,
        table_name=os.getenv('TABLE_NAME'),
        collection_name=os.getenv('COLLECTION_NAME')
    )

    return mongo_client, collection
