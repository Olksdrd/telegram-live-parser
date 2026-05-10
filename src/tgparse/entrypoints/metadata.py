import logging
import os

from tgparse.parsers import chat_metadata_parser, start_parser
from tgparse.utils.logging import init_logging
from tgparse.utils.repo.interface import RepoSpec

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    init_logging()

    parse_subcriptions = os.getenv('PARSE_SUBSCRIPTIONS') == 'yes'
    start_parser(
        chat_metadata_parser,
        session_backend=os.getenv('SESSION_DB_TYPE'),
        input_repo_spec=RepoSpec('json', os.getenv('NON_SUBBED_CHANNELS_LIST')),
        output_repo_spec=RepoSpec(os.getenv('CHATS_REPO'), os.getenv('CHATS_TABLE')),
        parse_subscriptions=parse_subcriptions,
    )
