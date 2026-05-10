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
from tgparse.utils.repo.interface import RepoSpec

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)

PARSER_TYPES = {
    'live': live_parser,
    'history': history_parser,
    'meta': chat_metadata_parser,
}


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
    input_group = parent_arg_parser.add_argument_group('Inputs')
    input_group.add_argument(
        '-c',
        '--chats-repository',
        help='Chats repository type (default: %(default)s)',
        default='cli',
        choices=['cli', 'json', 'mongodb'],
    )
    input_group.add_argument(
        '-i',
        '--input',
        help='Channels to parse',
        type=str,
        default='channels',
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

    live_arg_parser = subparsers.add_parser(  # noqa: F841
        'live',
        help='Near real-time parser',
        parents=[parent_arg_parser],
    )

    history_arg_parser = subparsers.add_parser(  # noqa: F841
        'history',
        help='Parse message history',
        parents=[parent_arg_parser],
    )

    channel_arg_parser = subparsers.add_parser(
        'meta',
        help='Generate channels list',
        parents=[parent_arg_parser],
    )
    channel_arg_parser.add_argument(
        '-s',
        '--parse-subscriptions',
        help='Add all subscriptions to channel DB',
        action='store_true',
        default=False,
    )

    args: Namespace = arg_parser.parse_args(argv)
    if 'parse_subscriptions' not in args:
        args.parse_subscriptions = False
    init_logging(min_log_level=get_log_level(args.verbose))

    start_parser(
        parser=PARSER_TYPES[args.command],
        session_backend=args.backend,
        input_repo_spec=RepoSpec(args.chats_repository, args.input),
        output_repo_spec=RepoSpec(args.repository, args.output),
        parse_subscriptions=args.parse_subscriptions,
    )

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
