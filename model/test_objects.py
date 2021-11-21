import pytest
import pytz

from datetime import datetime
from pathlib import Path
from typing import Dict, List
from model.objects import Blob, Commit, TreeNode, TreeNodeEntry

class TestBlob:
    def test_verify_encoded_data(self):
        improper_split_by_space = b'cant_split_by_space'
        improper_type = b'notblob 40\x00test'
        improper_split_by_null = b'blob 40 test'
        improper_content_length_format = b'blob notnumber\x00test'
        improper_content_length_of_data = b'blob 40\x00test'
        proper_data = b'blob 12\x00Hello World!'

        assert Blob.verify_encoded_data(improper_split_by_space) == False
        assert Blob.verify_encoded_data(improper_type) == False
        assert Blob.verify_encoded_data(improper_split_by_null) == False
        assert Blob.verify_encoded_data(improper_content_length_format) == False
        assert Blob.verify_encoded_data(improper_content_length_of_data) == False
        assert Blob.verify_encoded_data(proper_data) == True

    def test_decode(self):
        improper_content_length_of_data = b'blob 40\x00test'
        proper_data = b'blob 12\x00Hello World!'

        with pytest.raises(Exception):
            improper_blob = Blob.decode(improper_content_length_of_data)

        proper_blob = Blob.decode(proper_data)

        assert proper_blob.data == b'Hello World!'

    def test_encode(self):
        blob = Blob(b'Hello World!')

        assert blob.encode() == b'blob 12\x00Hello World!'
        assert blob.cached_encoded_data is not None


class TestNodeEntry:
    def test_encode(self):
        entry_one = TreeNodeEntry(
            Path('test_dir'),
            'abcd'*10,
            'tree',
            False,
            None,
        )
        entry_two = TreeNodeEntry(
            Path('dir/test.txt'),
            'abcd'*10,
            'blob',
            False,
            None,
        )
        entry_three = TreeNodeEntry(
            Path('test.sh'),
            'abcd'*10,
            'blob',
            True,
            None,
        )

        entry_one_byte_string = entry_one.encode()
        entry_two_byte_string = entry_two.encode()
        entry_three_byte_string = entry_three.encode()

        assert entry_one_byte_string == \
            b'40000 test_dir\x00' + bytes.fromhex('abcd'*10)
        assert entry_two_byte_string == \
            b'100644 test.txt\x00' + bytes.fromhex('abcd'*10)
        assert entry_three_byte_string == \
            b'100755 test.sh\x00' + bytes.fromhex('abcd'*10)

    def test_decode(self):
        entry_one_bytes = b'40000 test_dir\x00' + bytes.fromhex('abcd'*10)
        entry_two_bytes = b'100644 test.txt\x00' + bytes.fromhex('abcd'*10)
        entry_three_bytes = b'100755 test.sh\x00' + bytes.fromhex('abcd'*10)

        entry_one = TreeNodeEntry(
            Path('test_dir'),
            'abcd'*10,
            'tree',
            False,
            None,
        )
        entry_two = TreeNodeEntry(
            Path('dir/test.txt'),
            'abcd'*10,
            'blob',
            False,
            None,
        )
        entry_three = TreeNodeEntry(
            Path('test.sh'),
            'abcd'*10,
            'blob',
            True,
            None,
        )
        
        entry_one_decoded = TreeNodeEntry.decode(entry_one_bytes)
        entry_two_decoded = TreeNodeEntry.decode(entry_two_bytes)
        entry_three_decoded = TreeNodeEntry.decode(entry_three_bytes)

        assert entry_one == entry_one_decoded
        assert entry_two == entry_two_decoded
        assert entry_three == entry_three_decoded


class TestNode:
    def test_encode(self):
        tree_node_entries: Dict[str, TreeNodeEntry] = {}

        tree_node_entries['test_dir'] = TreeNodeEntry(
            Path('test_dir'),
            'abcd'*10,
            'tree',
            False,
            None,
        )
        tree_node_entries['test.txt'] = TreeNodeEntry(
            Path('test.txt'),
            'abcd'*10,
            'blob',
            False,
            None,
        )
        tree_node_entries['test'] = TreeNodeEntry(
            Path('test'),
            'abcd'*10,
            'tree',
            False,
            None,
        )

        tested_tree_node = TreeNode(tree_node_entries)

        assert tested_tree_node.encode() == \
            b'tree 102\x00' + \
            b'100644 test.txt\x00' + bytes.fromhex('abcd'*10) + \
            b'40000 test\x00' + bytes.fromhex('abcd'*10) + \
            b'40000 test_dir\x00' + bytes.fromhex('abcd'*10)
        assert tested_tree_node.cached_encoded_data is not None

    def test_decode(self):
        tree_bytes = \
            b'tree 102\x00' + \
            b'100644 test.txt\x00' + bytes.fromhex('abcd'*10) + \
            b'40000 test\x00' + bytes.fromhex('abcd'*10) + \
            b'40000 test_dir\x00' + bytes.fromhex('abcd'*10)

        tree_node_entries: Dict[str, TreeNodeEntry] = {}

        tree_node_entries['test_dir'] = TreeNodeEntry(
            Path('test_dir'),
            'abcd'*10,
            'tree',
            False,
            None,
        )
        tree_node_entries['test.txt'] = TreeNodeEntry(
            Path('test.txt'),
            'abcd'*10,
            'blob',
            False,
            None,
        )
        tree_node_entries['test'] = TreeNodeEntry(
            Path('test'),
            'abcd'*10,
            'tree',
            False,
            None,
        )

        decoded_tree = TreeNode.decode(tree_bytes)

        assert len(decoded_tree.entries) == 3
        assert 'test_dir' in decoded_tree.entries
        assert decoded_tree.entries['test_dir'] == tree_node_entries['test_dir']
        assert 'test.txt' in decoded_tree.entries
        assert decoded_tree.entries['test.txt'] == tree_node_entries['test.txt']
        assert 'test' in decoded_tree.entries
        assert decoded_tree.entries['test'] == tree_node_entries['test']


class TestCommit:
    def test_encode(self):
        date = datetime(2021, 8, 28, 16, 50, 13)
        commit = Commit(
            'Vasya Pupkin',
            'vasya@vpupkin.com',
            'First commit.',
            'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3',
            date,
            ''
        )
        timestamp: str = pytz.utc.localize(date).strftime('%s %z')
        author: bytes = b'Vasya Pupkin <vasya@vpupkin.com> ' + timestamp.encode() + b'\n'

        assert commit.encode() == \
            b'commit 178\x00' + \
            b'tree a94a8fe5ccb19ba61c4c0873d391e987982fbbd3\n' + \
            b'author ' + author + \
            b'committer ' + author + \
            b'\n' + \
            b'First commit.\n'

        assert commit.cached_encoded_data is not None

    def test_decode(self):
        date = datetime(2021, 8, 28, 16, 50, 13)
        timestamp: str = pytz.utc.localize(date).strftime('%s %z')
        author_bytes = b'Vasya Pupkin <vasya@vpupkin.com> ' + timestamp.encode() + b'\n'
        commit = Commit(
            'Vasya Pupkin',
            'vasya@vpupkin.com',
            'First commit.',
            'a94a8fe5ccb19ba61c4c0873d391e987982fbbd3',
            date,
            ''
        )
        commit_bytes = \
            b'commit 178\x00' + \
            b'tree a94a8fe5ccb19ba61c4c0873d391e987982fbbd3\n' + \
            b'author ' + author_bytes + \
            b'committer ' + author_bytes + \
            b'\n' + \
            b'First commit.\n'

        assert Commit.decode(commit_bytes) == commit

