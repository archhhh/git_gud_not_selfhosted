from pathlib import Path

from model.repo import Repo
from model.objects import TreeNode

def handle_list_head() -> None:
    try:
        current_path = Path.cwd()
        current_repo: Repo = Repo.get_current_repo(current_path)
        current_head = current_repo.read_head()
        current_commit = current_repo.read_commit(current_head)

        if current_commit != None:
            current_tree_node = current_commit.tree_oid
            current_commit_oid = current_commit.get_oid()

            current_tree = current_repo.read_tree(
                current_tree_node,
                [],
                Path(''),
                True,
            )

            if current_tree == None:
                current_tree = TreeNode({})

            print(f'Current commit {current_commit_oid}')

            current_tree.print_tree(Path(''))
    except Exception as exception:
        print(f'Fatal: {str(exception)}')
