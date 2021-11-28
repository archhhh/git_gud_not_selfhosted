from pathlib import Path

from model.repo import Repo

def handle_checkout(commit_oid: str):
    should_proceed = input('Your current work may be lost. Proceed? Y/N\n')

    if should_proceed == 'Y':
        try:
            current_path = Path.cwd()
            current_repo: Repo = Repo.get_current_repo(current_path)
            current_repo.checkout(commit_oid)
        except Exception as exception:
            print(f'Fatal: {str(exception)}')
