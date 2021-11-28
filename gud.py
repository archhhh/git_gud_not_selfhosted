import argparse

from handlers.init.init import handle_init
from handlers.commit.commit import handle_commit
from handlers.add.add import handle_add
from handlers.list_head.list_head import handle_list_head
from handlers.log.log import handle_log
from handlers.checkout.checkout import handle_checkout

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

    add_subparser: argparse.ArgumentParser = subparsers.add_parser(
        'add', 
        help='add help',
    )
    add_subparser.add_argument(
        'paths',
        nargs='+',
        default='paths to stage',
        help='list string paths',
    )

    list_head_subparser: argparse.ArgumentParser = subparsers.add_parser(
        'list-head', 
        help='list head files',
    )

    log_subparser: argparse.ArgumentParser = subparsers.add_parser(
        'log', 
        help='log commits starting from current',
    )

    checkout_subparser: argparse.ArgumentParser = subparsers.add_parser(
        'checkout', 
        help='checkout certain commit',
    )
    checkout_subparser.add_argument(
        'commit_id',
        nargs=1,
        help='id of the commit to be checked out'
    )

    args: argparse.Namespace = parser.parse_args()
    command: str = args.command
    
    if command == 'init':
        handle_init(args.path)

        exit(0)
    elif command == 'commit':
        handle_commit(args.m)

        exit(0)
    elif command == 'add':
        handle_add(args.paths)

        exit(0)
    elif command == 'list-head':
        handle_list_head()

        exit(0)
    elif command == 'log':
        handle_log()

        exit(0)
    elif command == 'checkout':
        handle_checkout(args.commit_id[0])

        exit(0)
    else:
        print('fatal: Unsupported command')

        exit(1)