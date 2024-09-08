from enum import StrEnum, auto
import importlib
import os

from dotenv import load_dotenv

from utils.repo.repository import Repository

load_dotenv('./env/config.env')


class RepositoryType(StrEnum):
    MONGODB = auto()
    DYNAMODB = auto()
    LOCAL_STORAGE = auto()


def repository_factory(repo_type: str = '') -> Repository:
    if repo_type == '':
        repo_type = os.getenv('REPOSITORY_TYPE')

    repo = importlib.import_module(f'utils.repo.{repo_type}')

    if repo_type == RepositoryType.MONGODB:
        return repo.MongoRepository(
            table_name=os.getenv('TABLE_NAME'),
            collection_name=os.getenv('COLLECTION_NAME'),
            user=os.getenv('DB_USER'),
            passwd=os.getenv('DB_PASSWD'),
            ip=os.getenv('DB_IP'),
            port=int(os.getenv('DB_PORT'))
        )
    elif repo_type == RepositoryType.DYNAMODB:
        return repo.DynamoRepository(
            table_name=os.getenv('TABLE_NAME'),
            region=os.getenv('AWS_REGION')
        )
    elif repo_type == RepositoryType.LOCAL_STORAGE:
        raise NotImplementedError
    else:
        raise ValueError
