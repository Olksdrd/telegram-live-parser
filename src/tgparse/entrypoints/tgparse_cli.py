import logging
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING

from tgparse.parsers import (
    chat_metadata_parser,
    history_parser,
    live_parser,
    start_parser,
)
from tgparse.utils.logging import init_logging
from tgparse.utils.parser_helpers import RepoSpec

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


def get_log_level(num_of_v: int) -> str:
    match num_of_v:
        case 0:
            return 'CRITICAL'
        case 1:
            return 'WARNING'
        case 2:
            return 'INFO'
        case _:
            return 'DEBUG'


def main(argv: Sequence[str] | None = None) -> int:
    parent_arg_parser = ArgumentParser(add_help=False, color=True)
    parent_arg_parser.add_argument(
        '-v',
        '--verbose',
        help='Increase output verbosity',
        action='count',
        default=0,
    )
    parent_arg_parser.add_argument(
        '-b',
        '--backend',
        help='Backend database to store session data (default: %(default)s)',
        default='sqlite',
        choices=['sqlite', 'mongodb'],
    )
    parent_arg_parser.add_argument(
        '-c',
        '--chats-repository',
        help='Chats repository type (default: %(default)s)',
        default='cli',
        choices=['cli', 'json', 'mongodb'],
    )
    output_group = parent_arg_parser.add_argument_group('Outputs')
    output_group.add_argument(
        '-r',
        '--repository',
        help='Storage type for parsed data (default: %(default)s)',
        default='cli',
        choices=['cli', 'json', 'mongodb'],
    )
    output_group.add_argument(
        '-o',
        '--output',
        help='Output file (without file extension) or database table name',
        # TODO: disable this option for cli
    )

    arg_parser = ArgumentParser(
        prog='tgparse',
        color=True,
    )
    subparsers = arg_parser.add_subparsers(
        required=True,
        dest='command',
    )

    live_arg_parser = subparsers.add_parser(
        'live',
        help='Near real-time parser',
        parents=[parent_arg_parser],
    )
    live_arg_parser.add_argument(
        '-i',
        '--input',
        help='Channels to parse',
        type=str,
        default='channels',
    )

    history_arg_parser = subparsers.add_parser(
        'history',
        help='Parse message history',
        parents=[parent_arg_parser],
    )
    history_arg_parser.add_argument(
        '-i',
        '--input',
        help='Channels to parse',
        type=str,
        default='channels',
    )

    channel_arg_parser = subparsers.add_parser(
        'channel',
        help='Generate channels list',
        parents=[parent_arg_parser],
    )
    channel_arg_parser.add_argument(
        '-a',
        '--additional-channels',
        help='List of channel names to add to channel DB',
        type=str,
    )
    channel_arg_parser.add_argument(
        '-s',
        '--parse-subscriptions',
        help='Add all subscriptions to channel DB',
        action='store_true',
        default=False,
    )
    channel_arg_parser.add_argument(
        '-l',
        '--channels-list-repository',
        help='Channels list repository type (default: %(default)s)',
        default='cli',
        choices=['cli', 'json', 'mongodb'],
    )

    args: Namespace = arg_parser.parse_args(argv)
    log_level = get_log_level(args.verbose)
    init_logging(min_log_level=log_level)

    match args.command:
        case 'live':
            start_parser(
                parser=live_parser,
                session_backend=args.backend,
                input_repo_spec=RepoSpec(args.chats_repository, args.input),
                output_repo_spec=RepoSpec(args.repository, args.output),
            )
        case 'history':
            start_parser(
                parser=history_parser,
                session_backend=args.backend,
                input_repo_spec=RepoSpec(args.chats_repository, args.input),
                output_repo_spec=RepoSpec(args.repository, args.output),
            )
        case 'channel':
            start_parser(
                parser=chat_metadata_parser,
                session_backend=args.backend,
                input_repo_spec=RepoSpec(args.channels_list_repository, args.additional_channels),
                output_repo_spec=RepoSpec(args.repository, args.output),
                parse_subscriptions=args.parse_subscriptions,
            )
        case _:
            pass

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
