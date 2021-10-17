import argparse

from handlers.init.init import handle_init
from handlers.commit.commit import handle_commit

if __name__ == '__main__':
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    subparsers: argparse._SubParsersAction = parser.add_subparsers(
        dest='command',
        help='gud supported commands',
    )

    init_subparser: argparse.ArgumentParser = subparsers.add_parser(
        'init', 
        help='init help',
    )
    init_subparser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='path to the new gud repository',
    )

    commit_subparser: argparse.ArgumentParser = subparsers.add_parser(
        'commit', 
        help='commit help',
    )
    commit_subparser.add_argument(
        'm',
        nargs='?',
        default='Default commit message',
        help='commit message',
    )

    args: argparse.Namespace = parser.parse_args()
    command: str = args.command
    
    if command == 'init':
        handle_init(args.path)

        exit(0)
    elif command == 'commit':
        handle_commit(args.m)

        exit(0)
