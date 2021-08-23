from __future__ import annotations
from typing import List, Union

class Object:
    @staticmethod
    def verify_encoded_data(encoded_data: bytes):
        pass

    @staticmethod
    def decode(encoded_data: bytes) -> Union[Object, None]:
        pass

    def encode(self) -> bytes:
        pass


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
        self.data: str = data

    def encode(self) -> bytes:
        data_as_bytes: bytes = self.data.encode('utf-8')
        len_of_data_as_bytes: str = str(len(data_as_bytes))
        full_content_as_bytes = b'blob ' + len_of_data_as_bytes.encode('utf-8') \
            + b'\x00' + data_as_bytes

        return full_content_as_bytes
