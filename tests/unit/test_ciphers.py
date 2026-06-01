import pytest

from canopus.cipher.aes256cbc import AES256CBCCipher
from canopus.cipher.aes256gcm import AES256GCMCipher
from canopus.cipher.fernet import FernetCipher


@pytest.mark.parametrize("cipher_class", [FernetCipher, AES256GCMCipher, AES256CBCCipher])
class TestCipherRoundtrip:

    def test_encrypt_decrypt_string(self, cipher_class):
        cipher = cipher_class()
        key = cipher.generate_key()
        data = b"hello canopus"
        assert cipher.decrypt(key, cipher.encrypt(key, data)) == data

    def test_encrypt_decrypt_json(self, cipher_class):
        cipher = cipher_class()
        key = cipher.generate_key()
        data = b'{"user": "waldo", "role": "admin"}'
        assert cipher.decrypt(key, cipher.encrypt(key, data)) == data

    def test_encrypt_produces_different_tokens(self, cipher_class):
        cipher = cipher_class()
        key = cipher.generate_key()
        data = b"same plaintext"
        # Each encryption should produce a unique token (random IV/nonce)
        assert cipher.encrypt(key, data) != cipher.encrypt(key, data)

    def test_decrypt_with_wrong_key_raises(self, cipher_class):
        cipher = cipher_class()
        key1 = cipher.generate_key()
        key2 = cipher.generate_key()
        token = cipher.encrypt(key1, b"secret")
        with pytest.raises((ValueError, Exception)):
            cipher.decrypt(key2, token)

    def test_generate_key_returns_bytes(self, cipher_class):
        cipher = cipher_class()
        key = cipher.generate_key()
        assert isinstance(key, bytes)
        assert len(key) > 0


class TestCipherAliases:

    def test_aliases_are_unique(self):
        aliases = {FernetCipher().alias, AES256GCMCipher().alias, AES256CBCCipher().alias}
        assert len(aliases) == 3

    def test_aliases_are_single_char(self):
        for cipher_class in [FernetCipher, AES256GCMCipher, AES256CBCCipher]:
            assert len(cipher_class().alias) == 1


class TestKeySizes:

    def test_fernet_key_size(self):
        # Fernet keys are 44 bytes (32 raw bytes in base64url)
        key = FernetCipher().generate_key()
        assert len(key) == 44

    def test_aes256gcm_key_size(self):
        key = AES256GCMCipher().generate_key()
        assert len(key) == 32

    def test_aes256cbc_key_size(self):
        # 32 bytes AES + 32 bytes HMAC
        key = AES256CBCCipher().generate_key()
        assert len(key) == 64
