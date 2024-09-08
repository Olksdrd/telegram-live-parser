from dataclasses import asdict

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

from utils.parser_helpers import CompactMessage
from utils.repo.repository import Repository


class MongoRepository(Repository[CompactMessage]):
    def __init__(
        self,
        table_name: str,
        collection_name: str,
        user: str,
        passwd: str,
        ip: str,
        port: int = 27017,
    ) -> None:
        self._db_uri = f'mongodb://{user}:{passwd}@{ip}:{port}'
        self.table_name = table_name
        self.collection_name = collection_name

    def connect(self) -> None:
        # logging.info('Connecting to database...')
        self.client = MongoClient(
            self._db_uri,
            connect=False,  # I think it still connects here
            serverSelectionTimeoutMS=10000  # 10 seconds
            )
        self._is_connected()
        # logging.info('Connection established.')
        db = self.client.get_database(self.table_name)
        self.collection = db.get_collection(self.collection_name)
        # return self

    def _is_connected(self) -> bool:
        try:
            self.client.server_info()
        except ServerSelectionTimeoutError:
            print('Failed to connect to the server.')

    def disconnect(self) -> None:
        self.client.close()

    def _convert_message_to_document(self, message: CompactMessage) -> dict:
        return asdict(message)

    def put_one(self, message: CompactMessage) -> str:
        document = self._convert_message_to_document(message)
        response = self.collection.insert_one(document)
        return f'Record ID: {response.inserted_id}.'
