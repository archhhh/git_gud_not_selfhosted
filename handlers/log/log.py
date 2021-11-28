from pathlib import Path

from model.repo import Repo
from model.objects import Commit, TreeNode, TreeNodeEntry

def handle_log() -> None:
    try:
        current_path = Path.cwd()
        current_repo: Repo = Repo.get_current_repo(current_path)
        current_head = current_repo.read_head()
        current_commit = current_repo.read_commit(current_head)

        while current_commit != None:
            print(f'{current_commit}')

            current_commit = current_repo.read_commit(current_commit.parent)
    except Exception as exception:
        print(f'Fatal: {str(exception)}')
