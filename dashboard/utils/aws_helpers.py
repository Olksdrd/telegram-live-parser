from pathlib import Path

import boto3
from dotenv import load_dotenv
from dynamodb_json import json_util as json
import pandas as pd

load_dotenv(dotenv_path=Path('./env/aws.env'))


def connect_to_dynamo(region: str = 'eu-central-1'):
    dynamodb = boto3.client('dynamodb', region_name=region)
    return dynamodb


def _preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df
        # .rename({
        #     'msg': 'Message',
        #     'date': 'Date',
        #     'chat_name': 'Chat_Name'
        # }, axis=1)
        .drop('ID', axis=1)
        .assign(Date=pd.to_datetime(df['Date'])
                # .dt.tz_localize(tz='UTC')
                # .dt.tz_convert(tz='Europe/Kyiv')
                .dt.strftime('%Y/%m/%d %H:%M:%S')
                )
        .sort_values(by='Date', ascending=False)
        [['Message', 'Date', 'Chat_Name']]
    )


def fetch_data(dynamodb) -> list[dict]:
    data = dynamodb.scan(
        TableName='TgParserData'
    )
    df = pd.DataFrame(json.loads(data['Items']))

    df = _preprocess_data(df)

    return df.to_dict('records')
