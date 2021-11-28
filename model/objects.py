from __future__ import annotations

import hashlib
import pytz

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Union


class Object:
    @staticmethod
    def verify_encoded_data(encoded_data: bytes):
        pass

    @staticmethod
    def decode(encoded_data: bytes) -> Object:
        pass

    @staticmethod
    def decode_header(encoded_header: bytes):
        split_header = encoded_header.split(b' ')

        if len(split_header) != 2:
            raise Exception('fatal: Invalid object header')
        
        type = split_header[0].decode('utf-8')
        len_of_data = int(split_header[1].decode('utf-8'))

        if type not in ['tree', 'blob', 'commit']:
            raise Exception('fatal: Invalid object type in header')

        return {'type': type, 'len_of_data': len_of_data}

    def __init__(self, type: str):
        self.type = type
        self.cached_encoded_data: Union[bytes, None] = None

    def encode_with_header(self, data: bytes) -> bytes:
        len_of_data_as_bytes: str = str(len(data))
        full_content_as_bytes = self.type.encode('utf-8') \
            + b' ' + len_of_data_as_bytes.encode('utf-8') \
            + b'\x00' + data

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
    def decode(encoded_data: bytes) -> Blob:
        if Blob.verify_encoded_data(encoded_data) == False:
            raise Exception('Invalid byte sequence')

        split_data = encoded_data.split(b'\x00', 1)
        header = Object.decode_header(split_data[0])
        
        if header['type'] != 'blob':
            raise Exception('fatal: Invalid blob data')

        data = split_data[1]

        return Blob(data)

    def __init__(self, data: bytes):
        super().__init__('blob')

        self.data: bytes = data

    def encode(self) -> bytes:
        if self.cached_encoded_data == None:
            self.cached_encoded_data = self.encode_with_header(self.data)

        assert not self.cached_encoded_data is None

        return self.cached_encoded_data


class TreeNodeEntry:
    def __init__(
        self, 
        path: Path,
        object_oid: str,
        object_type: str,
        is_executable: bool,
        content: Union[TreeNode, Blob, None],
    ):
        self.name = path.name
        self.type = object_type
        self.content = content
        self.oid = content.get_oid() if content else object_oid

        if self.type == 'tree':
            self.mode = '40000'
        elif self.type == 'blob':
            if is_executable:
                self.mode = '100755'
            else:
                self.mode = '100644'

    def __eq__(self, other):
        if not isinstance(other, TreeNodeEntry):
            return False

        return \
            self.name == other.name and \
            self.mode == other.mode and \
            self.oid == other.oid and \
            self.type == other.type

    def encode(self) -> bytes:
        return \
            bytes(f'{self.mode} {self.name}\x00', 'utf-8') \
            + bytes.fromhex(self.oid)

    @staticmethod
    def decode(encoded_data: bytes) -> TreeNodeEntry:
        split_data = encoded_data.split(b'\x00', 1)

        if len(split_data) != 2 or len(split_data[1]) != 20:
            raise Exception('fatal: Invalid byte sequence')

        [mode_bytes, name_bytes] = split_data[0].split(b' ')
        oid = split_data[1].hex()
        mode = mode_bytes.decode('utf-8')
        name = Path(name_bytes.decode('utf-8'))

        if mode not in ['100755', '100644', '40000']:
            raise Exception('fatal: Invalid mode string')
            
        is_executable = mode == '100755'
        type = 'blob' if mode.startswith('1') else 'tree' 

        return TreeNodeEntry(name, oid, type, is_executable, None)

    def add(self, entry: TreeNodeEntry, path_parts: Tuple[str, ...]):
        if self.type != 'tree':
            return

        if isinstance(self.content, Blob):
            return

        if self.content == None: 
            return

        self.content.add(entry, path_parts)
        self.oid = self.content.get_oid()


class TreeNode(Object):
    def __init__(
        self,
        entries: Dict[str, TreeNodeEntry]
    ):
        super().__init__('tree')

        self.entries = entries

    def encode(self) -> bytes:
        if self.cached_encoded_data == None:
            sorted_entries = sorted(
                self.entries.values(),
                key=lambda x: x.name + '/' if x.type == 'tree' else x.name
            )

            encoded_entries = map(
                lambda x: x.encode(), 
                sorted_entries,
            )
            data_as_bytes = b''.join(encoded_entries)
            self.cached_encoded_data = self.encode_with_header(data_as_bytes)

        assert not self.cached_encoded_data is None

        return self.cached_encoded_data

    @staticmethod
    def decode(encoded_data: bytes) -> TreeNode:
        split_data = encoded_data.split(b'\x00', 1)
        header = Object.decode_header(split_data[0])
        
        if header['type'] != 'tree':
            raise Exception('fatal: Invalid data')

        ptr = 0
        encoded_entries = split_data[1]
        actual_len_of_data = 0
        entries: Dict[str, TreeNodeEntry] = {}

        while ptr < len(encoded_entries):
            split_encoded_entry = encoded_entries[ptr:].split(b'\x00', 1)

            if len(split_encoded_entry) != 2 or len(split_encoded_entry[1]) < 20:
                raise Exception('fatal: Invalid data')

            entry_bytes = b'\x00'.join([split_encoded_entry[0], split_encoded_entry[1][:20]])
            entry = TreeNodeEntry.decode(entry_bytes)
            len_of_encoded_entry = len(entry_bytes)     
   
            entries[entry.name] = entry

            actual_len_of_data += len(entry_bytes)
            ptr += len_of_encoded_entry

        if actual_len_of_data != header['len_of_data']:
            raise Exception('fatal: length doesn\'t match')

        return TreeNode(entries)

    def add(self, entry: TreeNodeEntry, path_parts: Tuple[str, ...]):
        if len(path_parts) == 0:
            return

        self.cached_encoded_data = None

        current_part = path_parts[0]
        rest_parts = path_parts[1:]

        if len(rest_parts) == 0:
            self.entries[current_part] = entry

            return

        if current_part not in self.entries or self.entries[current_part].type != 'tree' or self.entries[current_part].content is None:
            node = TreeNode({})

            node.add(entry, rest_parts)

            self.entries[current_part] = TreeNodeEntry(
                Path(current_part),
                node.get_oid(),
                'tree',
                False,
                node
            )
        else:
            self.entries[current_part].add(entry, rest_parts)


class Commit(Object):
    def __init__(
        self,
        name: str,
        email: str,
        message: str,
        tree_oid: str,
        date: datetime,
        parent: str,
    ):
        super().__init__('commit')

        self.name = name
        self.email = email
        self.message = message
        self.tree_oid = tree_oid
        self.timestamp = pytz.utc.localize(date).strftime('%s %z')
        self.parent = parent

    def __eq__(self, other):
        if not isinstance(other, Commit):
            return False

        return \
            self.name == other.name and \
            self.email == other.email and \
            self.message == other.message and \
            self.tree_oid == other.tree_oid and \
            self.timestamp == other.timestamp and \
            self.parent == other.parent 

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

            if self.parent != '':
                lines.insert(1, f'parent {self.parent}')

            data_as_bytes = '\n'.join(lines).encode()
            self.cached_encoded_data = self.encode_with_header(data_as_bytes)

        assert not self.cached_encoded_data is None

        return self.cached_encoded_data

    @staticmethod
    def decode(encoded_data: bytes) -> Commit:
        split_data = encoded_data.split(b'\x00', 1)
        header = Object.decode_header(split_data[0])

        if header['type'] != 'commit':
            raise Exception('fatal: Invalid header type')

        split_content = split_data[1].split(b'\n')
        
        if len(split_content) != 6 and len(split_content) != 7:
            raise Exception('fatal: Invalid number of commit entries')

        tree_oid = ''
        name = ''
        email = ''
        timestamp = ''
        message = ''
        parent = ''

        tree_line_split = split_content[0].split(b' ')

        if len(tree_line_split) != 2 or tree_line_split[0] != b'tree' or \
           len(tree_line_split[1]) != 40:
            raise Exception('fatal: Invalid tree line in commit') 
        
        tree_oid = tree_line_split[1].decode('utf-8')

        if len(split_content) == 7:
            parent_line_split = split_content[1].split(b' ')

            if len(parent_line_split) != 2 or parent_line_split[0] != b'parent' or \
               len(parent_line_split[1]) != 40:
                raise Exception('fatal: Invalid parent line in commit') 

            parent = parent_line_split[1].decode('utf-8')

            del split_content[1]

        author_line_split = split_content[1].split(b' ', 1)

        if len(author_line_split) != 2 or author_line_split[0] != b'author':
            raise Exception('fatal: Invalid author line in commit')

        author_data = author_line_split[1]
    
        timestamp_start = author_data.rfind(b'> ') + 2
        email_start = author_data.rfind(b' <') + 2

        name = author_data[:email_start - 2].decode('utf-8')
        email = author_data[email_start:timestamp_start - 2].decode('utf-8')
        timestamp = author_data[timestamp_start:].decode('utf-8')
        timestamp_int = int(timestamp.split(' ')[0])

        message = split_content[4].decode('utf-8')

        return Commit(
            name,
            email,
            message,
            tree_oid,
            datetime.fromtimestamp(timestamp_int),
            parent
        )