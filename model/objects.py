from __future__ import annotations

import hashlib

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
        self.cached_encoded_data: Union[bytes, None] = None

    def encode(self) -> bytes:
        if self.cached_encoded_data == None:
            data_as_bytes: bytes = self.data.encode('utf-8')
            len_of_data_as_bytes: str = str(len(data_as_bytes))
            full_content_as_bytes = b'blob ' + len_of_data_as_bytes.encode('utf-8') \
                + b'\x00' + data_as_bytes

            self.cached_encoded_data = full_content_as_bytes

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

    def to_byte_string(self):
        return \
            bytes(f'{self.mode} {self.name} ', 'utf-8') \
            + bytes.fromhex(self.oid)


class TreeNode(Object):
    @staticmethod
    def decode(encoded_data: bytes) -> Union[TreeNode, None]:
        pass

    def __init__(self, entries: List[TreeNodeEntry]):
        super().__init__('tree')

        self.cached_encoded_data: Union[bytes, None] = None
        self.entries = sorted(entries, key = lambda x: x.name)
    
    def encode(self):
        if self.cached_encoded_data == None:
            entries_to_byte_string: List[bytes] = map(
                lambda x: x.to_byte_string(), 
                self.entries,
            )
            data_as_bytes = b''.join(entries_to_byte_string)
            len_of_data_as_bytes: str = str(len(data_as_bytes))
            full_content_as_bytes = b'tree ' + len_of_data_as_bytes.encode('utf-8') \
                + b'\x00' + data_as_bytes

            self.cached_encoded_data = full_content_as_bytes

        assert not self.cached_encoded_data is None

        return self.cached_encoded_data