"""Interface for saving channels or messages to MondoDB"""

import logging
from collections.abc import Mapping

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class MongoRepository:
    def __init__(
        self,
        table_name: str,
        collection_name: str,
        user: str,
        passwd: str,
        ip: str,
        port: int = 27017,
        **kwargs,
    ) -> None:
        self._db_uri = f"mongodb://{user}:{passwd}@{ip}:{port}"
        self.table_name = table_name
        self.collection_name = collection_name

    def connect(self) -> None:
        logger.info("Connecting to MongoDB...")
        self.client = MongoClient(
            self._db_uri,
            connect=False,  # I think it still connects here
            serverSelectionTimeoutMS=10000,  # 10 seconds
        )
        self._is_connected()
        db = self.client.get_database(self.table_name)
        self.collection = db.get_collection(self.collection_name)
        logger.info("Connection to MongoDB established.")

    def _is_connected(self) -> bool:
        try:
            self.client.server_info()
        except ServerSelectionTimeoutError:
            logger.critical("Failed to connect to the server.")

    def disconnect(self) -> None:
        self.client.close()
        logger.info("MongoDB connection closed.")

    def _convert_message_to_document(self, message: Mapping) -> dict:
        return {str(key): val for key, val in message.items() if val}

    def put_one(self, object: Mapping) -> str:
        document = self._convert_message_to_document(object)
        if document:  # no need to put empty docs
            response = self.collection.insert_one(document)
            return f"Record ID: {response.inserted_id}."
        else:
            logger.warning("Document was empty. Skipping inserting to MongoDB...")
            return "Skipped empty"

    def put_many(self, objects: list[Mapping]) -> str:
        docs = [self._convert_message_to_document(msg) for msg in objects]
        non_empty_docs = [doc for doc in docs if doc]  # filter out empty docs
        if docs != non_empty_docs:
            num_of_empty_docs = len(docs) - len(non_empty_docs)
            logger.warning(f"Skipping {num_of_empty_docs} empty documents...")
        if non_empty_docs:  # can't put an empty list to MongoDB
            response = self.collection.insert_many(non_empty_docs)
            return f"Inserted {len(non_empty_docs)} objects. {response}"
        else:
            logger.error(
                "Can't put an empty list to a database. Skipping inserting to MongoDB..."
            )
            return "Failed to insert any document"

    def get_all(self) -> list[Mapping]:
        objects_list = list(self.collection.find())

        return objects_list
