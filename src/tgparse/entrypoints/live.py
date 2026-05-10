import logging
import os

from tgparse.parsers import live_parser, start_parser
from tgparse.utils.logging import init_logging
from tgparse.utils.parser_helpers import RepoSpec

logger = logging.getLogger(__name__)


if __name__ == '__main__':
    init_logging()

    start_parser(
        live_parser,
        session_backend=os.getenv('SESSION_DB_TYPE'),
        input_repo_spec=RepoSpec(os.getenv('CHATS_REPO'), os.getenv('CHATS_TABLE')),
        output_repo_spec=RepoSpec(os.getenv('MESSAGE_REPO'), os.getenv('MESSAGE_TABLE')),
    )
