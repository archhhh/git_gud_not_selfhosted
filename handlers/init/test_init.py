from unittest.mock import patch
from pathlib import Path

from handlers.init.init import create_paths

class TestInit():
    def test_create_paths(self):
        base_path = Path('test_base_path')
        directories = ['dir1', 'dir2']
        paths = create_paths(base_path, directories)

        assert len(paths) == 2
        assert str(paths[0]) == 'test_base_path/dir1'
        assert str(paths[1]) == 'test_base_path/dir2'
