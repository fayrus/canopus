from cryptography.fernet import Fernet, InvalidToken

from canopus.cipher.base import CipherBackend


class FernetCipher(CipherBackend):
    """AES-128-CBC + HMAC-SHA256. Default cipher — general purpose."""
    alias = 'f'

    def generate_key(self) -> bytes:
        return Fernet.generate_key()

    def encrypt(self, key: bytes, data: bytes) -> str:
        return Fernet(key).encrypt(data).decode()

    def decrypt(self, key: bytes, token: str) -> bytes:
        try:
            return Fernet(key).decrypt(token.encode())
        except InvalidToken:
            raise ValueError("Decryption failed")
