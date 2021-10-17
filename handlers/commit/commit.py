from datetime import datetime
from pathlib import Path

from utils.constants import GIT_AUTHOR_EMAIL, GIT_AUTHOR_NAME
from model.repo import Repo
from model.objects import Commit, TreeNode

def handle_commit(commit_message: str = 'Default commit message') -> None:
    try:
        current_path = Path.cwd()
        current_repo: Repo = Repo.get_current_repo(current_path)
        built_tree: TreeNode = current_repo.build_tree(current_repo.repo_path)
        parent: str = current_repo.read_head()

        commit: Commit = Commit(
            GIT_AUTHOR_NAME,
            GIT_AUTHOR_EMAIL,
            commit_message,
            built_tree.get_oid(),
            datetime.utcnow(),
            parent
        )

        current_repo.write_object(commit)
        current_repo.update_head(commit.get_oid())

        print(f'Created new commit with oid {commit.get_oid()}')
    except Exception as exception:
        print(f'Fatal: {str(exception)}')
