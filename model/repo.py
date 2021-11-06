import zlib
import os

from pathlib import Path
from typing import List

from model.objects import Object, TreeNode, Blob, TreeNodeEntry, TreeNode
from model.misc import RepoObjPath
from utils.constants import STORAGE_DIRECTORY


class Repo:
    @staticmethod
    def init_repo(path: Path):
        path = path.resolve()

        storage_path = path.joinpath(STORAGE_DIRECTORY)

        if storage_path.is_dir():
            raise Exception('fatal: already a git repository')

        objects_to_create: List[RepoObjPath] = [
            RepoObjPath(storage_path.joinpath('objects'), 'dir'),
            RepoObjPath(storage_path.joinpath('ref'), 'dir'),
            RepoObjPath(storage_path.joinpath('index'), 'file'),
            RepoObjPath(storage_path.joinpath('config'), 'file'),
            RepoObjPath(storage_path.joinpath('HEAD'), 'file')
        ]

        for object in objects_to_create:
            try: 
                object.create_obj()
            except Exception as exc:
                print(str(exc))

                exit(1)

        print(f'Initialized empty git repository in {str(path)}')

    @staticmethod
    def get_current_repo(current_path: Path):
        current_path_obj = current_path.resolve()
        prev_path_obj = None

        while current_path_obj != prev_path_obj:
            if current_path_obj.joinpath(STORAGE_DIRECTORY).is_dir():
                return Repo(current_path_obj)
            
            prev_path_obj = current_path_obj
            current_path_obj = current_path_obj.parent
        
        raise Exception('fatal: not a git repository (or any of the parent directories): .git')

    def __init__(self, path: Path):
        self.repo_path = path
        self.storage_path: Path = self.repo_path.resolve().joinpath(STORAGE_DIRECTORY)
        self.head_path: Path = self.storage_path.joinpath('HEAD')

        if not self.storage_path.is_dir(): 
            raise Exception('fatal: not a git repository (or any of the parent directories): .git')

    def read_head(self) -> str:
        try:
            head_content = self.head_path.read_text()

            return head_content
        except:
            raise Exception('fatal: cannot open HEAD file')

    def update_head(self, value: str) -> None:
        # need to support locks to allow multiple processes access
        # HEAD file
        head_path = self.storage_path.joinpath('HEAD')

        try: 
            with open(str(head_path), 'w') as file:
                file.write(value)
                file.close()
        except:
            raise Exception('fatal: cant write to HEAD')

    def write_object(self, object: Object) -> None:
        encoded_data = object.encode()
        object_id = object.get_oid()
        compressed_encoded_data = zlib.compress(encoded_data)
        dir_name = object_id[0:2]
        file_name = object_id[2:]
        objects_path = self.storage_path.joinpath('objects').joinpath(dir_name)
        temp_object_path = objects_path.joinpath(f'temp_obj_{file_name}')

        try:
            objects_path.mkdir(parents=True, exist_ok=True)

            with open(str(temp_object_path), 'wb+') as file:
                file.write(compressed_encoded_data)
                file.close()

            temp_object_path.rename(objects_path.joinpath(file_name))
        except: 
            raise Exception(f'fatal: cannot write object with type {object.type} and oid {object.get_oid()}')

    def build_tree(self, current_path: Path) -> TreeNode:
        ignore: List[str] = [
            STORAGE_DIRECTORY,
            '.mypy_cache',
            '.pytest_cache',
            '__pycache__',
            '.git',
        ]

        list_of_entries: List[TreeNodeEntry] = []

        for child_path in current_path.iterdir():            
            if child_path.name in ignore:
                continue

            current_object: Object = Object('dummy')

            if child_path.is_dir():
                current_object = self.build_tree(child_path.resolve())
            else:
                current_object = Blob(child_path.read_bytes())
                self.write_object(current_object)

            list_of_entries.append(
                TreeNodeEntry(
                    child_path,
                    current_object.get_oid(),
                    current_object.type,
                    os.access(str(child_path.resolve()), os.X_OK)
                )
            )   

        current_tree: TreeNode = TreeNode(list_of_entries)

        self.write_object(current_tree)

        return current_tree    
            