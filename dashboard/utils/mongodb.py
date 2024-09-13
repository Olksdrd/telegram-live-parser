import pandas as pd
from pymongo import MongoClient
from pymongo.collection import Collection


class MongoFetcher:
    def __init__(
        self,
        table_name: str,
        collection_name: str,
        user: str,
        passwd: str,
        ip: str,
        port: str,
    ) -> None:
        self.db_uri = f"mongodb://{user}:{passwd}@{ip}:{port}"
        self.table_name = table_name
        self.collection_name = collection_name

    def _get_mongo_client(self) -> MongoClient:
        return MongoClient(self.db_uri)

    def _get_collection(self, client: MongoClient) -> Collection:
        db = client.get_database(self.table_name)
        return db.get_collection(self.collection_name)

    def connect(self) -> None:
        self.client = self._get_mongo_client()

        self.collection = self._get_collection(self.client)

    @staticmethod
    def _preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.drop("_id", axis=1)
            .assign(
                date=df["date"]
                .dt.tz_localize(tz="UTC")
                .dt.tz_convert(tz="Europe/Kyiv")
                .dt.strftime("%Y/%m/%d %H:%M:%S")
            )
            .rename(
                {"msg": "Message", "date": "Date", "chat_name": "Chat_Name"}, axis=1
            )
            .sort_values(by="Date", ascending=False)[["Message", "Date", "Chat_Name"]]
        )

    def get_data(self) -> list[dict]:
        df = pd.DataFrame(
            list(
                self.collection.find(
                    filter={}, projection={"msg": 1, "date": 1, "chat_name": 1}
                )
            )
        )

        df = self._preprocess_data(df)

        return df.to_dict("records")
