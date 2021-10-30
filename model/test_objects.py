import pytest
import pytz

from datetime import datetime
from pathlib import Path
from typing import List
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
    def test_to_byte_string(self):
        entry_one = TreeNodeEntry(
            Path('test_dir'),
            'abcd'*10,
            'tree',
            False,
        )
        entry_two = TreeNodeEntry(
            Path('dir/test.txt'),
            'abcd'*10,
            'blob',
            False
        )
        entry_three = TreeNodeEntry(
            Path('test.sh'),
            'abcd'*10,
            'blob',
            True
        )

        entry_one_byte_string = entry_one.to_byte_string()
        entry_two_byte_string = entry_two.to_byte_string()
        entry_three_byte_string = entry_three.to_byte_string()

        assert entry_one_byte_string == \
            b'40000 test_dir\x00' + bytes.fromhex('abcd'*10)
        assert entry_two_byte_string == \
            b'100644 test.txt\x00' + bytes.fromhex('abcd'*10)
        assert entry_three_byte_string == \
            b'100755 test.sh\x00' + bytes.fromhex('abcd'*10)


class TestNode:
    def test_encode(self):
        tree_node_entries: List[TreeNodeEntry] = []

        tree_node_entries.append(
            TreeNodeEntry(
                Path('test_dir'),
                'abcd'*10,
                'tree',
                False,
            )
        )
        tree_node_entries.append(
            TreeNodeEntry(
                Path('test.txt'),
                'abcd'*10,
                'blob',
                False
            )
        )

        tested_tree_node = TreeNode(tree_node_entries)

        assert tested_tree_node.encode() == \
            b'tree 71\x00' + \
            b'100644 test.txt\x00' + bytes.fromhex('abcd'*10) + \
            b'40000 test_dir\x00' + bytes.fromhex('abcd'*10)
        assert tested_tree_node.cached_encoded_data is not None


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

