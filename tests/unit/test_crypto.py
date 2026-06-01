import pytest

from canopus.cipher.aes256cbc import AES256CBCCipher
from canopus.cipher.aes256gcm import AES256GCMCipher
from canopus.cipher.fernet import FernetCipher
from canopus.core import crypto, keys
from canopus.storage.local_file import LocalFileBackend


@pytest.fixture(autouse=True)
def setup_context(tmp_path):
    """Initialize keys and cipher before each test."""
    cipher = FernetCipher()
    backend = LocalFileBackend(str(tmp_path / "keys.txt"))
    keys.init(backend, cipher)
    crypto.init_cipher(cipher)


class TestEncryptData:

    def test_encrypt_string(self):
        result = crypto.encrypt_data({'plaintext': 'hello'})
        assert result['status'] == 'success'
        assert result['data']['ciphertext'].startswith('canopus:v0:f:')

    def test_encrypt_integer(self):
        result = crypto.encrypt_data({'plaintext': 42})
        assert result['status'] == 'success'

    def test_encrypt_dict(self):
        result = crypto.encrypt_data({'plaintext': {'user': 'waldo'}})
        assert result['status'] == 'success'

    def test_encrypt_list(self):
        result = crypto.encrypt_data({'plaintext': [1, 2, 3]})
        assert result['status'] == 'success'

    def test_encrypt_missing_plaintext(self):
        result = crypto.encrypt_data({})
        assert result['status'] == 'error'
        assert result['data']['code'] == 'MISSING_FIELD'

    def test_encrypt_unsupported_type(self):
        result = crypto.encrypt_data({'plaintext': 3.14})
        assert result['status'] == 'error'
        assert result['data']['code'] == 'UNSUPPORTED_TYPE'

    def test_encrypt_invalid_key_version(self):
        result = crypto.encrypt_data({'plaintext': 'hello'}, key_version=99)
        assert result['status'] == 'error'
        assert result['data']['code'] == 'INVALID_KEY_VERSION'

    def test_encrypt_with_explicit_key_version(self):
        result = crypto.encrypt_data({'plaintext': 'hello'}, key_version=0)
        assert result['status'] == 'success'
        assert ':v0:' in result['data']['ciphertext']


class TestDecryptData:

    def test_decrypt_string(self):
        ct = crypto.encrypt_data({'plaintext': 'hello'})['data']['ciphertext']
        result = crypto.decrypt_data(ct)
        assert result['status'] == 'success'
        assert result['data']['plaintext'] == 'hello'

    def test_decrypt_dict(self):
        ct = crypto.encrypt_data({'plaintext': {'k': 'v'}})['data']['ciphertext']
        result = crypto.decrypt_data(ct)
        assert result['status'] == 'success'
        assert result['data']['plaintext'] == {'k': 'v'}

    def test_decrypt_integer(self):
        ct = crypto.encrypt_data({'plaintext': 99})['data']['ciphertext']
        result = crypto.decrypt_data(ct)
        assert result['status'] == 'success'
        assert result['data']['plaintext'] == 99

    def test_decrypt_invalid_ciphertext(self):
        result = crypto.decrypt_data('canopus:v0:f:notvalidtoken')
        assert result['status'] == 'error'
        assert result['data']['code'] == 'INVALID_CIPHERTEXT'

    def test_decrypt_bad_format(self):
        result = crypto.decrypt_data('not-a-canopus-ciphertext')
        assert result['status'] == 'error'
        assert result['data']['code'] == 'INVALID_CIPHERTEXT'

    def test_decrypt_unknown_cipher_alias(self):
        result = crypto.decrypt_data('canopus:v0:z:sometoken')
        assert result['status'] == 'error'
        assert result['data']['code'] == 'INVALID_CIPHERTEXT'

    def test_decrypt_key_version_out_of_range(self):
        result = crypto.decrypt_data('canopus:v99:f:sometoken')
        assert result['status'] == 'error'
        assert result['data']['code'] == 'INVALID_CIPHERTEXT'

    def test_decrypt_legacy_format(self):
        """Ciphertexts without cipher alias should default to Fernet."""
        ct = crypto.encrypt_data({'plaintext': 'legacy'})['data']['ciphertext']
        # Strip cipher alias: canopus:v0:f:token → canopus:v0:token
        parts = ct.split(':', 3)
        legacy = f"{parts[0]}:{parts[1]}:{parts[3]}"
        result = crypto.decrypt_data(legacy)
        assert result['status'] == 'success'
        assert result['data']['plaintext'] == 'legacy'


@pytest.mark.parametrize("cipher_class", [FernetCipher, AES256GCMCipher, AES256CBCCipher])
class TestEncryptDecryptPerCipher:

    def test_roundtrip(self, cipher_class, tmp_path):
        cipher = cipher_class()
        backend = LocalFileBackend(str(tmp_path / f"keys_{cipher.alias}.txt"))
        keys.init(backend, cipher)
        crypto.init_cipher(cipher)

        ct = crypto.encrypt_data({'plaintext': {'cipher': cipher.alias}})['data']['ciphertext']
        assert f':v0:{cipher.alias}:' in ct

        result = crypto.decrypt_data(ct)
        assert result['status'] == 'success'
        assert result['data']['plaintext'] == {'cipher': cipher.alias}
