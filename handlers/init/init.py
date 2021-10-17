from typing import List
from pathlib import Path

from model.repo import Repo

def handle_init(repo_path: str) -> None:
    Repo.init_repo(Path(repo_path))
