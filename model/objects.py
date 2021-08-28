from __future__ import annotations

import hashlib
import pytz

from datetime import datetime
from typing import Literal, List, Union


class Object:
    @staticmethod
    def verify_encoded_data(encoded_data: bytes):
        pass

    @staticmethod
    def decode(encoded_data: bytes) -> Union[Object, None]:
        pass

    def __init__(self, type: str):
        self.type = type
        self.cached_encoded_data: Union[bytes, None] = None

    def encode_with_header(self, data_as_bytes: bytes) -> bytes:
        len_of_data_as_bytes: str = str(len(data_as_bytes))
        full_content_as_bytes = self.type.encode('utf-8') \
            + b' ' + len_of_data_as_bytes.encode('utf-8') \
            + b'\x00' + data_as_bytes

        return full_content_as_bytes

    def encode(self) -> bytes:
        pass

    def get_oid(self) -> str:
        return hashlib.sha1(self.encode()).hexdigest()


class Blob(Object):
    @staticmethod
    def verify_encoded_data(encoded_data: bytes) -> bool:
        split_bytes_by_space = encoded_data.split(b' ', 1)

        if len(split_bytes_by_space) < 2:
            return False

        encoded_data_type = split_bytes_by_space[0].decode()

        if encoded_data_type != 'blob':
            return False

        split_bytes_by_null = split_bytes_by_space[1].split(b'\x00', 1)

        if len(split_bytes_by_null) < 2:
            return False

        data_length_str = split_bytes_by_null[0].decode()

        if not data_length_str.isnumeric():
            return False

        data_length = int(data_length_str)
        data_as_bytes = split_bytes_by_null[1]

        if data_length != len(data_as_bytes):
            return False

        return True

    @staticmethod
    def decode(encoded_data: bytes) -> Union[Blob, None]:
        if Blob.verify_encoded_data(encoded_data) == False:
            raise Exception('Invalid byte sequence')
        
        data = encoded_data.split(b' ', 1)[1].split(b'\x00')[1].decode()

        return Blob(data)

    def __init__(self, data: str):
        super().__init__('blob')

        self.data: str = data

    def encode(self) -> bytes:
        if self.cached_encoded_data == None:
            data_as_bytes: bytes = self.data.encode('utf-8')
            self.cached_encoded_data = self.encode_with_header(data_as_bytes)

        assert not self.cached_encoded_data is None

        return self.cached_encoded_data


class TreeNodeEntry:
    def __init__(
        self, 
        name: str, 
        oid: str, 
        mode: str, 
        type: Union[Literal['blob'], Literal['tree']],
    ):
        self.mode = mode
        self.name = name
        self.oid = oid
        self.type = type

    def to_byte_string(self) -> bytes:
        return \
            bytes(f'{self.mode} {self.name} ', 'utf-8') \
            + bytes.fromhex(self.oid)


class TreeNode(Object):
    @staticmethod
    def decode(encoded_data: bytes) -> Union[TreeNode, None]:
        pass

    def __init__(self, entries: List[TreeNodeEntry]):
        super().__init__('tree')

        self.entries = sorted(entries, key = lambda x: x.name)
    
    def encode(self) -> bytes:
        if self.cached_encoded_data == None:
            entries_to_byte_string: map[bytes] = map(
                lambda x: x.to_byte_string(), 
                self.entries,
            )
            data_as_bytes = b''.join(entries_to_byte_string)
            self.cached_encoded_data = self.encode_with_header(data_as_bytes)

        assert not self.cached_encoded_data is None

        return self.cached_encoded_data


class Commit(Object):
    def __init__(
        self,
        name: str,
        email: str,
        message: str,
        tree_oid: str,
        date: datetime,
        parent: Union[str, None] = None,
    ):
        super().__init__('commit')

        self.name = name
        self.email = email
        self.message = message
        self.tree_oid = tree_oid
        self.timestamp = pytz.utc.localize(date).strftime('%s %z')
        self.parent = parent
    
    def encode(self) -> bytes:
        if self.cached_encoded_data == None:
            author = f'{self.name} <{self.email}> {self.timestamp}'

            lines: List[str] = [
                f'tree {self.tree_oid}',
                f'author {author}',
                f'committer {author}',
                '',
                self.message + '\n',
            ]

            if self.parent != None:
                lines.insert(1, f'parent {self.parent}')

            data_as_bytes = '\n'.join(lines).encode()
            self.cached_encoded_data = self.encode_with_header(data_as_bytes)

        assert not self.cached_encoded_data is None

        return self.cached_encoded_data