import importlib
import os
from typing import Protocol


class DataFetcher(Protocol):

    def connect(self) -> None:
        pass

    def get_data(self) -> list[dict]:
        pass


def data_fetcher(repo_type: str) -> DataFetcher:
    repo = importlib.import_module(f"utils.{repo_type}")

    if repo_type == "mongodb":
        return repo.MongoFetcher(
            table_name=os.getenv("TABLE_NAME"),
            collection_name=os.getenv("COLLECTION_NAME"),
            user=os.getenv("DB_USER"),
            passwd=os.getenv("DB_PASSWD"),
            ip=os.getenv("DB_IP"),
            port=int(os.getenv("DB_PORT")),
        )
    elif repo_type == "dynamodb":
        return repo.DynamoFetcher(
            table_name=os.getenv("TABLE_NAME"), region=os.getenv("AWS_REGION")
        )
    else:
        raise ValueError
