import pytest

from model.objects import Blob

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

        assert proper_blob.data == 'Hello World!'

    def test_encode(self):
        blob = Blob('Hello World!')

        assert blob.encode() == b'blob 12\x00Hello World!'