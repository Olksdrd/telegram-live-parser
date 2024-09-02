import os
from pathlib import Path

from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path('./env/config.env'))


def connect_to_db(user, passwd, ip, port):
    db_uri = f'mongodb://{user}:{passwd}@{ip}:{port}'
    mongo_client = MongoClient(db_uri)
    return mongo_client


def get_db_collection(client, table_name, collection_name):
    db = client.get_database(table_name)
    collection = db.get_collection(collection_name)
    return collection


def connect_to_mongo():
    mongo_client = connect_to_db(
        user=str(os.environ.get('DB_USER')),
        passwd=str(os.environ.get('DB_PASSWD')),
        ip=os.environ.get('DB_IP'),
        port=os.environ.get('DB_PORT')
    )

    collection = get_db_collection(
        client=mongo_client,
        table_name=os.environ.get('TABLE_NAME'),
        collection_name=os.environ.get('COLLECTION_NAME')
        )
    return mongo_client, collection
