import pytest

from pathlib import Path
from model.repo import Repo
from model.misc import RepoObjPath

class TestRepoObjPath:
    def test_create_obj(self, fs):
        test_path_dir = Path('/testing/')
        test_path_file = Path('/testing/what/file')

        test_path_dir_obj = RepoObjPath(test_path_dir, 'dir')
        test_path_file_obj = RepoObjPath(test_path_file, 'file')
        
        test_path_dir_obj.create_obj()
        test_path_file_obj.create_obj()

        assert test_path_dir.exists() == True
        assert test_path_dir.is_dir() == True

        assert test_path_file.exists() == True
        assert test_path_file.is_dir() == False
