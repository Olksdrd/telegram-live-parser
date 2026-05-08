import logging
from argparse import ArgumentParser, Namespace
from typing import Sequence

from tgparse.channel_parser import start_history_parser
from tgparse.form_chats_list import start_chat_metadata_parser
from tgparse.live_parser import start_live_parser
from tgparse.utils.logging import init_logging

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
    parent_parser = ArgumentParser(add_help=False, color=True)
    parent_parser.add_argument(
        '-v',
        '--verbose',
        help='Increase output verbosity',
        action='count',
        default=0,
    )
    parent_parser.add_argument(
        '-b',
        '--backend',
        help='Backend database to store session data (default: %(default)s)',
        default='sqlite',
        choices=['sqlite', 'mongodb'],
    )
    parent_parser.add_argument(
        '-c',
        '--chats-repository',
        help='Chats to repository backend',
        default='local',
        choices=['cli', 'local', 'mongodb'],
    )
    output_group = parent_parser.add_argument_group('Outputs')
    output_group.add_argument(
        '-r',
        '--repository',
        help='Storage type for parsed data (default: %(default)s)',
        default='cli',
        choices=['cli', 'local', 'parquet', 'mongodb'],
    )
    output_group.add_argument(
        '-o',
        '--output',
        # TODO: remove file extension from local
        help='Output file (without file extension) or database table name',
        # TODO: disable this option for cli
    )

    parser = ArgumentParser(
        prog='tgparse',
        color=True,
    )
    subparsers = parser.add_subparsers(
        required=True,
        dest='command',
    )

    live_parser = subparsers.add_parser(
        'live',
        help='Near real-time parser',
        parents=[parent_parser],
    )
    live_parser.add_argument(
        '-i',
        '--input',
        help='Channels to parse',
        type=str,
        default='channels',
    )

    history_parser = subparsers.add_parser(
        'history',
        help='Parse message history',
        parents=[parent_parser],
    )
    history_parser.add_argument(
        '-i',
        '--input',
        help='Channels to parse',
        type=str,
        default='channels',
    )

    channel_parser = subparsers.add_parser(
        'channel',
        help='Generate channels list',
        parents=[parent_parser],
    )
    channel_parser.add_argument(
        '-a',
        '--additional-channels',
        help='JSON list of channel names to add to channel DB',
        type=str,
    )
    channel_parser.add_argument(
        '-s',
        '--parse-subscriptions',
        help='Add all subscriptions to channel DB',
        action='store_true',
    )

    args: Namespace = parser.parse_args(argv)
    log_level = get_log_level(args.verbose)
    init_logging(min_log_level=log_level)

    match args.command:
        case 'live':
            start_live_parser(
                session_backend=args.backend,
                chats_repository=args.chats_repository,
                chats_path=args.input,
                message_repository=args.repository,
                output_path=args.output,
            )
        case 'history':
            start_history_parser(
                session_backend=args.backend,
                chats_repository=args.chats_repository,
                chats_path=args.input,
                message_repository=args.repository,
                output_path=args.output,
            )
        case 'channel':
            start_chat_metadata_parser(
                session_backend=args.backend,
                chats_repository=args.chats_repository,
                chats_path=args.output,
                additional_channels=args.additional_channels,
                parse_subscriptions=args.parse_subscriptions,
            )
        case _:
            pass

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
