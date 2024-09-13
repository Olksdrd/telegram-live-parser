import boto3
import pandas as pd
from dynamodb_json import json_util as json


class DynamoFetcher:
    def __init__(self, table_name: str, region: str = "eu-central-1") -> None:
        self.region = region
        self.table_name = table_name

    def connect(self) -> None:
        self.dynamodb = boto3.client("dynamodb", region_name=self.region)

    @staticmethod
    def _preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
        return (
            df
            # .rename({
            #     "msg": "Message",
            #     "date": "Date",
            #     "chat_name": "Chat_Name"
            # }, axis=1)
            .drop("ID", axis=1)
            .assign(
                Date=pd.to_datetime(df["Date"])
                # .dt.tz_localize(tz="UTC")
                # .dt.tz_convert(tz="Europe/Kyiv")
                .dt.strftime("%Y/%m/%d %H:%M:%S")
            )
            .sort_values(by="Date", ascending=False)[["Message", "Date", "Chat_Name"]]
        )

    def get_data(self) -> list[dict]:
        data = self.dynamodb.scan(TableName="TgParserData")
        df = pd.DataFrame(json.loads(data["Items"]))

        df = self._preprocess_data(df)

        return df.to_dict("records")
