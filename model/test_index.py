from pathlib import Path

import hashlib
from os import stat_result
from model.index import Index, IndexEntry

class TestIndexEntry:
    def test_validate_data(self, fs):
        valid_test_string = \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00'

        assert IndexEntry.validate_data(valid_test_string) == True

        invalid_test_string_len = \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00'
        
        assert IndexEntry.validate_data(invalid_test_string_len) == False

        invalid_test_string_mode = \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa5\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c'
        
        assert IndexEntry.validate_data(invalid_test_string_mode) == False

        invalid_test_string_total_len = \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa5\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0d' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00'

        assert IndexEntry.validate_data(invalid_test_string_total_len) == False

    def test_encode(self, fs):
        test_path = Path('dir/test.txt')
        
        test_index_entry = IndexEntry(
            test_path,
            False,
            'abcd'*10,
            15601023,
            20193,
            2053,
            472220,
            1000,
            1000,
            81
        )

        test_string = \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00'

        assert test_index_entry.encode() == test_string
    
    def test_decode(self, fs):
        test_string = \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00'

        test_index_entry = IndexEntry.decode(test_string)

        assert test_index_entry.ctime_s == 15601023
        assert test_index_entry.ctime_ns == 0
        assert test_index_entry.mtime_s == 20193
        assert test_index_entry.mtime_ns == 0
        assert test_index_entry.dev == 2053
        assert test_index_entry.ino == 472220
        assert test_index_entry.uid == 1000
        assert test_index_entry.gid == 1000
        assert test_index_entry.file_size == 81
        assert test_index_entry.mode == int('100644', 8)
        assert test_index_entry.path == 'dir/test.txt'
        assert test_index_entry.oid == 'abcd'*10


class TestIndex:
    def test_validate_data(self, fs):
        valid_data = \
            b'DIRC\x00\x00\x00\x02\x00\x00\x00\x01' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00'
    
        valid_data_checksum = bytes.fromhex(hashlib.sha1(valid_data).hexdigest())

        assert Index.validate_data(valid_data + valid_data_checksum) == True

        invalid_data_signature = \
            b'DIasRC\x00\x00\x00\x02\x00\x00\x00\x01' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00'

        assert Index.validate_data(invalid_data_signature) == False

        invalid_data_checksum = \
            b'DIRC\x00\x00\x00\x02\x00\x00\x00\x01' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00' + \
            b'\x00'*20

        assert Index.validate_data(invalid_data_checksum) == False

        invalid_data_number_of_entries = \
            b'DIRC\x00\x00\x00\x02\x00\x00\x00\x04' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00'
        checksum = bytes.fromhex(hashlib.sha1(invalid_data_number_of_entries).hexdigest())

        assert Index.validate_data(invalid_data_number_of_entries + checksum) == False 

        valid_data_multiple_entries = \
            b'DIRC\x00\x00\x00\x02\x00\x00\x00\x02' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0f' + \
            bytes('dir/testerf.txt', 'utf-8') + \
            b'\x00\x00\x00'

        checksum = bytes.fromhex(hashlib.sha1(valid_data_multiple_entries).hexdigest())

        assert Index.validate_data(valid_data_multiple_entries + checksum) == True

    def test_add_entry(self, fs):
        index_path = Path('/index').resolve()
        index = Index(index_path)

        valid_entry_one = IndexEntry(
            Path('test/dir'),
            False,
            'abcd'*10,
            15601023,
            20193,
            2053,
            472220,
            1000,
            1000,
            81
        )

        valid_entry_two = IndexEntry(
            Path('test/dir/test'),
            False,
            'abcd'*10,
            15601023,
            20193,
            2053,
            472220,
            1000,
            1000,
            81
        )
        
        index._add_entry(valid_entry_one)

        assert len(index.entries) == 1 and 'test/dir' in index.entries

        index._add_entry(valid_entry_two)

        assert len(index.entries) == 1 and 'test/dir/test' in index.entries

        with open(str(index_path), 'wb+', 0) as index_file:
            index_file.close()

        stat = index_path.stat()
        stat.st_ctime = 15601023
        stat.st_mtime = 20193
        stat.st_dev = 2053
        stat.st_ino = 472220
        stat.st_uid = 1000
        stat.st_gid = 1000
        stat.st_rsize = 81

        index.add_entry(
            Path('test/dir'),
            'abcd'*10,
            stat,
            False,
        )
        
        assert len(index.entries) == 1 and 'test/dir' in index.entries
        assert index.entries['test/dir'].ctime_s == valid_entry_one.ctime_s
        assert index.entries['test/dir'].ctime_ns == valid_entry_one.ctime_ns
        assert index.entries['test/dir'].mtime_s == valid_entry_one.mtime_s
        assert index.entries['test/dir'].mtime_ns == valid_entry_one.mtime_ns
        assert index.entries['test/dir'].dev == valid_entry_one.dev
        assert index.entries['test/dir'].ino == valid_entry_one.ino
        assert index.entries['test/dir'].uid == valid_entry_one.uid
        assert index.entries['test/dir'].gid == valid_entry_one.gid
        assert index.entries['test/dir'].file_size == valid_entry_one.file_size
        assert index.entries['test/dir'].mode == valid_entry_one.mode 
        assert index.entries['test/dir'].path == valid_entry_one.path
        assert index.entries['test/dir'].oid == valid_entry_one.oid
    
    def test_read_index(self, fs):
        index_path = Path('/index').resolve()

        valid_data_multiple_entries = \
            b'DIRC\x00\x00\x00\x02\x00\x00\x00\x02' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0f' + \
            bytes('dir/testerf.txt', 'utf-8') + \
            b'\x00\x00\x00'
    
        checksum = bytes.fromhex(hashlib.sha1(valid_data_multiple_entries).hexdigest())

        with open(str(index_path), 'wb+', 0) as index_file:
            index_file.write(valid_data_multiple_entries + checksum)
            index_file.close()

        index = Index.read_index(index_path)
        
        assert str(index.index_path) == str(index_path)
        assert len(index.entries) == 2

        for path in ['dir/test.txt', 'dir/testerf.txt']:
            assert path in index.entries

            test_entry = index.entries[path]
            valid_entry = IndexEntry(
                Path(path),
                False,
                'abcd'*10,
                15601023,
                20193,
                2053,
                472220,
                1000,
                1000,
                81
            )

            assert test_entry.ctime_s == valid_entry.ctime_s
            assert test_entry.ctime_ns == valid_entry.ctime_ns
            assert test_entry.mtime_s == valid_entry.mtime_s
            assert test_entry.mtime_ns == valid_entry.mtime_ns
            assert test_entry.dev == valid_entry.dev
            assert test_entry.ino == valid_entry.ino
            assert test_entry.uid == valid_entry.uid
            assert test_entry.gid == valid_entry.gid
            assert test_entry.file_size == valid_entry.file_size
            assert test_entry.mode == valid_entry.mode 
            assert test_entry.path == valid_entry.path
            assert test_entry.oid == valid_entry.oid
    
    def test_encode(self, fs):
        index = Index(Path('/index').resolve())

        for path in ['dir/test.txt', 'dir/testerf.txt']:
            entry = IndexEntry(
                Path(path),
                False,
                'abcd'*10,
                15601023,
                20193,
                2053,
                472220,
                1000,
                1000,
                81
            )

            index._add_entry(entry)

        valid_data_multiple_entries = \
            b'DIRC\x00\x00\x00\x02\x00\x00\x00\x02' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0c' + \
            bytes('dir/test.txt', 'utf-8') + \
            b'\x00\x00\x00\x00\x00\x00' + \
            b'\x00\xee\x0d\x7f\x00\x00\x00\x00' + \
            b'\x00\x00\x4e\xe1\x00\x00\x00\x00' + \
            b'\x00\x00\x08\x05\x00\x07\x34\x9c' + \
            b'\x00\x00\x81\xa4\x00\x00\x03\xe8' + \
            b'\x00\x00\x03\xe8\x00\x00\x00\x51' + \
            b'\xab\xcd'*10 + b'\x00\x0f' + \
            bytes('dir/testerf.txt', 'utf-8') + \
            b'\x00\x00\x00'

        checksum = bytes.fromhex(hashlib.sha1(valid_data_multiple_entries).hexdigest())
        
        assert index.encode() == valid_data_multiple_entries + checksum
