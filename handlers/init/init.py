from typing import List
from pathlib import Path

def create_paths(base: Path, dirs: List[str]) -> List[Path]:
    dir_path_object: List[Path] = []

    for dir in dirs:
        dir_path_object.append(base.joinpath(dir))
    
    return dir_path_object

def handle_init(repo_path: str) -> None:
    base_git_path_obj: Path = Path(repo_path + '/.git').resolve()
    git_subdirectories: List[str] = ['objects', 'refs']
    full_git_subdirectories_path_objs: List[Path] = create_paths(
        base_git_path_obj,
        git_subdirectories,
    )

    for path in full_git_subdirectories_path_objs:
        try: 
            path.mkdir(parents=True)
        except Exception:
            print('Fatal Error')

            exit(1)

    print(f'Initialized empty jit repository in {base_git_path_obj}')
