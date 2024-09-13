import boto3

from utils.message_helpers import CompactMessage


class DynamoRepository:
    def __init__(self, table_name: str, region: str = "eu-central-1", **kwargs) -> None:
        self.region = region
        self.table_name = table_name

    def connect(self) -> None:
        self.client = boto3.client("dynamodb", region_name=self.region)

    def _is_connected(self) -> bool:
        pass

    def disconnect(self) -> None:
        self.client.close()

    def _convert_message_to_document(self, message: CompactMessage) -> dict:
        # TODO: make names uniform for all DBs if possible
        return {
            "ID": {"S": f"{message.chat_id}_{message.msg_id}"},
            "Message": {"S": message.msg},
            "Date": {"S": message.date.isoformat()},
            "Chat_Name": {"S": message.chat_name},
        }

    def put_one(self, message: CompactMessage) -> str:
        document = self._convert_message_to_document(message)
        response = self.client.put_item(TableName=self.table_name, Item=document)
        return f'Response status: {response["ResponseMetadata"]["HTTPStatusCode"]}.'  # noqa: E501
