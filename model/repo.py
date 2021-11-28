import zlib
import os

from pathlib import Path
from typing import List, Union

from model.index import Index
from model.objects import Commit, Object, TreeNode, Blob, TreeNodeEntry, TreeNode
from model.misc import RepoObjPath


class Repo:
    @staticmethod
    def init_repo(path: Path):
        path = path.resolve()

        storage_path = path.joinpath('.gitgud')

        if storage_path.is_dir():
            raise Exception('fatal: already a git repository')

        objects_to_create: List[RepoObjPath] = [
            RepoObjPath(storage_path.joinpath('objects'), 'dir'),
            RepoObjPath(storage_path.joinpath('ref'), 'dir'),
            RepoObjPath(storage_path.joinpath('index'), 'file'),
            RepoObjPath(storage_path.joinpath('config'), 'file'),
            RepoObjPath(storage_path.joinpath('HEAD'), 'file'),
            RepoObjPath(storage_path.joinpath('ref/main'), 'file'),
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
            if current_path_obj.joinpath('.gitgud').is_dir():
                return Repo(current_path_obj)
            
            prev_path_obj = current_path_obj
            current_path_obj = current_path_obj.parent
        
        raise Exception('fatal: not a git repository (or any of the parent directories): .git')

    def __init__(self, path: Path):
        self.repo_path = path
        self.storage_path: Path = self.repo_path.resolve().joinpath('.gitgud')
        self.head_path: Path = self.storage_path.joinpath('HEAD')
        self.index: Index = Index.read_index(self.storage_path.joinpath('index'))

        self.ignore: List[str] = [
            '.gitgud',
            '.mypy_cache',
            '.pytest_cache',
            '__pycache__',
            '.git',
        ]

        if not self.storage_path.is_dir(): 
            raise Exception('fatal: not a git repository (or any of the parent directories): .git')

    def read_head(self) -> str:
        try:
            head_content = self.head_path.read_text()

            return head_content
        except:
            raise Exception('fatal: cannot open HEAD file')

    def read_main(self) -> str:
        try:
            main_content = self.storage_path.joinpath('ref/main').read_text()

            return main_content
        except:
            raise Exception('fatal: cannot open main ref file')

    def update_main(self, value: str) -> None:
        main_path = self.storage_path.joinpath('ref/main')

        try: 
            with open(str(main_path), 'w') as file:
                file.write(value)
                file.close()
        except:
            raise Exception('fatal: cant write to main ref file')

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

    def read_commit(
        self,
        commit_oid: str,
    ) -> Union[Commit, None]:
        if len(commit_oid) == 0:
            return None

        if len(commit_oid) != 40:
            raise Exception('fatal: Invalid commit_oid')

        try:
            commit_oid_bytes = bytes.fromhex(commit_oid)
        except:
            raise Exception('fatal: Invalid commit_oid')

        commit_dir = commit_oid[:2]
        commit_file = commit_oid[2:]
        commit_path = self.storage_path \
                .joinpath('objects') \
                .joinpath(commit_dir) \
                .joinpath(commit_file)

        try:
            commit_content = zlib.decompress(commit_path.read_bytes())
        except:
            raise Exception('fatal: Cannot open commit file')

        return Commit.decode(commit_content)

    def read_tree(
        self,
        tree_oid: str,
        paths_to_include: List[Path],
        current_path: Path,
        should_include_all: bool,
    ) -> Union[TreeNode, None]:
        if len(tree_oid) == 0:
            return None

        if len(tree_oid) != 40:
            raise Exception('fatal: Invalid tree_oid')

        try:
            tree_oid_bytes = bytes.fromhex(tree_oid)
        except:
            raise Exception('fatal: Invalid tree_oid')

        tree_dir = tree_oid[0:2]
        tree_file = tree_oid[2:]

        try:
            tree_file_path = self.storage_path \
                .joinpath('objects') \
                .joinpath(tree_dir) \
                .joinpath(tree_file)

            tree_content = zlib.decompress(tree_file_path.read_bytes())
        except:
            raise Exception('fatal: Cannot open tree file')

        tree_node = TreeNode.decode(tree_content)

        for entry_key in tree_node.entries:
            entry = tree_node.entries[entry_key]

            if entry.type == 'tree':
                should_include_entry = should_include_all
                entry_full_path = current_path.joinpath(entry_key)

                for path_to_include in paths_to_include:
                    should_include_entry = should_include_entry or \
                        str(path_to_include).startswith(
                            str(entry_full_path)
                        )

                if should_include_entry:
                    entry_tree_node = self.read_tree(
                        entry.oid,
                        paths_to_include,
                        current_path.joinpath(entry_key),
                        should_include_all
                    )

                    entry_tree_node_entry = TreeNodeEntry(
                        Path(entry_key),
                        entry.oid,
                        'tree',
                        False,
                        entry_tree_node,
                    )

                    tree_node.entries[entry_key] = entry_tree_node_entry

        return tree_node

    def write_tree(self, tree: TreeNode):
        self.write_object(tree)

        for entry_key in tree.entries:
            if tree.entries[entry_key].type == 'tree' and isinstance(tree.entries[entry_key].content, TreeNode):
                self.write_tree(tree.entries[entry_key].content)


    def add_to_index(self, paths: List[Path]):
        resolved_paths: List[Path] = []

        for path in paths:
            path_str = str(path)
            repo_path_str = str(self.repo_path)

            if not path_str.startswith(repo_path_str):
                raise Exception(f'fatal: Arg {path} is not a part of repo')

            if path.is_dir():
                resolved_paths.extend(path.glob('**/*'))
            elif path.is_file():
                resolved_paths.append(path)

        for resolved_path in resolved_paths:
            relative_path = Path(str(resolved_path)[len(repo_path_str + '/'):])

            if resolved_path.is_dir() or resolved_path.name in self.ignore:
                continue

            should_ignore = False

            for parent in relative_path.parents:
                if parent.name in self.ignore:           
                    should_ignore = True
                    break

            if not should_ignore:
                current_object = Blob(resolved_path.read_bytes())

                self.write_object(current_object)
                self.index.add_entry(
                    relative_path,
                    current_object.get_oid(),
                    resolved_path.stat(),
                    os.access(str(resolved_path), os.X_OK)
                )

        self.index.write()
