import os
from pathlib import Path

import pandas as pd
from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv


load_dotenv(dotenv_path=Path('./env/config.env'))


def _get_mongo_client(
    user: str, passwd: str, ip: str, port: str
) -> MongoClient:
    db_uri = f'mongodb://{user}:{passwd}@{ip}:{port}'
    return MongoClient(db_uri)


def _get_collection(
    client: MongoClient,
    table_name: str,
    collection_name: str
) -> Collection:
    db = client.get_database(table_name)
    return db.get_collection(collection_name)


def connect_to_mongo() -> tuple[MongoClient, Collection]:
    mongo_client = _get_mongo_client(
        user=str(os.getenv('DB_USER')),
        passwd=str(os.getenv('DB_PASSWD')),
        ip=os.getenv('DB_IP'),
        port=os.getenv('DB_PORT')
    )

    collection = _get_collection(
        client=mongo_client,
        table_name=os.getenv('TABLE_NAME'),
        collection_name=os.getenv('COLLECTION_NAME')
    )

    return mongo_client, collection


def fetch_data(collection: Collection) -> list[dict]:
    df = (pd.DataFrame(list(
        collection.find(
            filter={},
            projection={'msg': 1, 'date': 1, 'chat_name': 1}
            )
        ))
    ).rename({
        'msg': 'Message',
        'date': 'Date',
        'chat_name': 'Chat_Name'
    }, axis=1)

    df = (
        df.drop('_id', axis=1)
        .assign(Date=pd.to_datetime(
            df
            ['Date']
            .dt.tz_localize(tz='UTC')
            .dt.tz_convert(tz='Europe/Kyiv')
            .dt.strftime('%Y/%m/%d %H:%M:%S')
            ))
        .sort_values(by='Date', ascending=False)
        [['Message', 'Date', 'Chat_Name']]
    )

    return df.to_dict('records')
