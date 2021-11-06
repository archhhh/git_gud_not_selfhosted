from __future__ import annotations

import hashlib
from os import stat_result
from pathlib import Path
from typing import Dict

class IndexEntry:
    def __init__(
        self,
        path: Path,
        is_executable: bool,
        oid: str,
        st_ctime: int,
        st_mtime: int,
        st_dev: int,
        st_ino: int,
        st_uid: int,
        st_gid: int,
        st_rsize: int,
    ): 
        self.ctime_s = st_ctime
        self.ctime_ns = 0
        self.mtime_s = st_mtime
        self.mtime_ns = 0
        self.dev = st_dev
        self.ino = st_ino
        self.uid = st_uid
        self.gid = st_gid
        self.file_size = st_rsize

        if is_executable:
            self.mode = int('100755', 8)
        else:
            self.mode = int('100644', 8)

        self.oid = oid
        self.path = str(path)

    @staticmethod
    def validate_data(data: bytes) -> bool:
        fixed_meta_info_len = 62
        fixed_meta_info = data[0:fixed_meta_info_len]

        if len(fixed_meta_info) != fixed_meta_info_len:
            return False

        mode = int(data[24:28].hex(), 16)
        path_len = int(data[60:62].hex(), 16)

        if mode != int('100644', 8) and mode != int('100755', 8):
            return False

        total_len_without_padding = fixed_meta_info_len + path_len
        padding_len = (8 - total_len_without_padding % 8)
        total_len = total_len_without_padding + padding_len

        if len(data) != total_len:
            return False

        padding = data[total_len_without_padding:total_len]

        if padding != b'\x00'*padding_len:
            return False

        return True

    def encode(self) -> bytes:
        encoded_without_pads = \
            self.ctime_s.to_bytes(4, 'big') + \
            self.ctime_ns.to_bytes(4, 'big') + \
            self.mtime_s.to_bytes(4, 'big') + \
            self.mtime_ns.to_bytes(4, 'big') + \
            self.dev.to_bytes(4, 'big') + \
            self.ino.to_bytes(4, 'big') + \
            self.mode.to_bytes(4, 'big') + \
            self.uid.to_bytes(4, 'big') + \
            self.gid.to_bytes(4, 'big') + \
            self.file_size.to_bytes(4, 'big') + \
            bytes.fromhex(self.oid) + \
            bytes(len(self.path).to_bytes(2, 'big')) + \
            bytes(self.path, 'utf-8')

        len_without_pads = 62 + len(str(self.path))

        encoded_with_pads = encoded_without_pads + b'\x00'*(8 - len_without_pads % 8)

        return encoded_with_pads

    @staticmethod
    def decode(data: bytes) -> IndexEntry:
        if not IndexEntry.validate_data(data):
            raise Exception('fatal: Corrupted IndexEntry')

        ctime = int(data[0:4].hex(), 16)
        ctime_ns = int(data[4:8].hex(), 16)
        mtime = int(data[8:12].hex(), 16)
        mtime_ns = int(data[12:16].hex(), 16)
        dev = int(data[16:20].hex(), 16)
        ino = int(data[20:24].hex(), 16)
        mode = int(data[24:28].hex(), 16)
        uid = int(data[28:32].hex(), 16)
        gid = int(data[32:36].hex(), 16)
        file_size = int(data[36:40].hex(), 16)
        oid = data[40:60].hex()
        path_len = int(data[60:62].hex(), 16)
        path = data[62:(62 + path_len)].decode('utf-8')

        is_executable = True if mode == int('100755', 8) else False

        return IndexEntry(
            Path(path),
            is_executable,
            oid,
            ctime,
            mtime,
            dev,
            ino,
            uid,
            gid,
            file_size
        )

class Index:
    def __init__(
        self,
        index_path: Path,
    ):
        self.entries: Dict[str, IndexEntry] = {}
        self.index_path = index_path.resolve()

    @staticmethod
    def validate_data(data: bytes) -> bool:
        # TODO: verify oids and path_names
    
        header = data[0:12]

        if len(header) != 12:
            return False

        signature = header[0:4].decode('utf-8')
        version = int(header[4:8].hex(), 16)
        number_of_entries = int(header[8:12].hex(), 16)

        if signature != 'DIRC': 
            return False

        current_byte_offset = 12

        for _ in range(number_of_entries):
            fixed_entry_info_len = 62
            fixed_entry_info = data[current_byte_offset:current_byte_offset + fixed_entry_info_len]

            if len(fixed_entry_info) != fixed_entry_info_len:
                return False

            path_len = int(fixed_entry_info[-2:].hex(), 16)
            total_len_without_padding = fixed_entry_info_len + path_len
            total_len = total_len_without_padding + (8 - total_len_without_padding % 8)
            entry_info = data[current_byte_offset:current_byte_offset + total_len]

            if len(entry_info) != total_len:
                return False

            if not IndexEntry.validate_data(entry_info):
                return False
            
            current_byte_offset += total_len

        if len(data) != current_byte_offset + 20:
            return False

        checksum = data[current_byte_offset:current_byte_offset + 20].hex()
        content_without_checksum = data[0: current_byte_offset]
        actual_checksum = hashlib.sha1(content_without_checksum).hexdigest()

        if checksum != actual_checksum:
            return False

        return True

    @staticmethod
    def read_index(index_path: Path) -> Index:
        index_path = index_path.resolve()

        try: 
            with open(str(index_path), 'rb') as index_file:
                index_file_content = index_file.read()
        except:
            raise Exception('fatal: Cant read index file')

        print(index_file_content)

        if not Index.validate_data(index_file_content):
            raise Exception('fatal: Corrupted index file')

        header = index_file_content[0:12]
        number_of_entries = int(header[8:12].hex(), 16)

        current_byte_offset = 12

        index = Index(index_path)

        for _ in range(number_of_entries):
            fixed_entry_info_len = 62
            fixed_entry_info = index_file_content[current_byte_offset:current_byte_offset + fixed_entry_info_len]
            path_len = int(fixed_entry_info[-2:].hex(), 16)
            total_len_without_padding = fixed_entry_info_len + path_len
            total_len = total_len_without_padding + (8 - total_len_without_padding % 8)
            entry_info = index_file_content[current_byte_offset:current_byte_offset + total_len]

            entry = IndexEntry.decode(entry_info)

            current_byte_offset += total_len

            index._add_entry(entry)

        return index

    def _add_entry(self, entry: IndexEntry):
        self.discard_conflicts(entry)
        self.entries[str(entry.path)] = entry

    def discard_conflicts(self, entry: IndexEntry) -> None:
        current_path = Path(entry.path).parent

        while str(current_path) != '.':
            if str(current_path) in self.entries:
                del self.entries[str(current_path)]

            current_path = current_path.parent

        entry_keys = self.entries.keys()

        for key in list(entry_keys):
            if self.entries[key].path.startswith(str(entry.path) + '/') \
               and key in self.entries:
                del self.entries[key]

    def add_entry(
        self,
        path: Path,
        oid: str,
        stat: stat_result,
        is_executable: bool,
    ) -> None:
        entry = IndexEntry(
            path,
            is_executable,
            oid,
            int(stat.st_ctime),
            int(stat.st_mtime),
            stat.st_dev,
            stat.st_ino,
            stat.st_uid,
            stat.st_gid,
            stat.st_rsize
        )

        self.discard_conflicts(entry)

        self.entries[str(entry.path)] = entry

    def encode(self) -> bytes:
        signature = b'DIRC'
        version = 2
        data = \
            signature + \
            version.to_bytes(4, 'big') + \
            len(self.entries).to_bytes(4, 'big')
        
        for entry_key in self.entries:
            data += self.entries[entry_key].encode()

        checksum = bytes.fromhex(hashlib.sha1(data).hexdigest())

        return data + checksum

    def write(self) -> None:
        encoded_data = self.encode()
        temp_path = self.index_path.joinpath('.tmp')

        try:
            temp_path.mkdir(parents=True, exist_ok=True)

            with open(str(temp_path), 'wb+') as file:
                file.write(encoded_data)
                file.close()

            temp_path.rename(self.index_path)
        except: 
            raise Exception('fatal: Cannot write index')
