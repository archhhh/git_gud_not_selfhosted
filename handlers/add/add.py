from pathlib import Path
from typing import List
from model.repo import Repo

def handle_add(paths: List[str]):
    try:
        current_workdir = Path.cwd()
        current_repo: Repo = Repo.get_current_repo(current_workdir)

        print('Current index')
        print(current_repo.index)

        resolved_paths: List[Path] = []

        for path in paths:
            full_path = current_workdir.joinpath(path).resolve()

            resolved_paths.append(full_path)

        current_repo.add_to_index(resolved_paths)

        print('New index')
        print(current_repo.index)
    except Exception as exc:
        print(str(exc))