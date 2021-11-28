from datetime import datetime
from pathlib import Path

from model.repo import Repo
from model.objects import Commit, TreeNode, TreeNodeEntry

def handle_commit(commit_message: str = 'Default commit message') -> None:
    try:
        current_path = Path.cwd()
        current_repo: Repo = Repo.get_current_repo(current_path)
        current_index = current_repo.index
        current_head = current_repo.read_head()
        current_commit = current_repo.read_commit(current_head)
        current_tree_node = '' if current_commit == None else current_commit.tree_oid
  
        current_index_entries_paths = list(map(
            lambda entry: Path(entry),
            current_index.entries.keys()
        ))

        current_tree = current_repo.read_tree(
            current_tree_node,
            current_index_entries_paths,
            Path(''),
            False,
        )

        if current_tree == None:
            current_tree = TreeNode({})

        for index_entry_key in current_index.entries:
            index_entry = current_index.entries[index_entry_key]
            index_entry_path = Path(index_entry_key)

            tree_node_entry = TreeNodeEntry(
                index_entry_path,
                index_entry.oid,
                'blob',
                index_entry.mode == int('100755', 8),
                None
            )

            current_tree.add(tree_node_entry, index_entry_path.parts)

        current_repo.write_tree(current_tree)

        commit: Commit = Commit(
            'test_name',
            'test_email',
            commit_message,
            current_tree.get_oid(),
            datetime.utcnow(),
            current_head
        )

        current_repo.write_object(commit)
        current_repo.update_head(commit.get_oid())
        current_index.clear()

        print(f'Created new commit with oid {commit.get_oid()}')
    except Exception as exception:
        print(f'Fatal: {str(exception)}')
