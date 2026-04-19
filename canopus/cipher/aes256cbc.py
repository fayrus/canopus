import base64
import hashlib
import hmac
import os

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from canopus.cipher.base import CipherBackend


class AES256CBCCipher(CipherBackend):
    """
    AES-256-CBC + HMAC-SHA256.
    Conservative option for FIPS 140-2 environments.
    Key size: 64 bytes (32 AES + 32 HMAC). IV size: 16 bytes.
    Token layout: base64url(iv[16] + ciphertext + hmac[32])
    """
    alias = 'c'

    def generate_key(self) -> bytes:
        return os.urandom(64)

    def encrypt(self, key: bytes, data: bytes) -> str:
        aes_key, hmac_key = key[:32], key[32:]
        iv = os.urandom(16)

        padder = padding.PKCS7(128).padder()
        padded = padder.update(data) + padder.finalize()

        encryptor = Cipher(algorithms.AES(aes_key), modes.CBC(iv)).encryptor()
        ciphertext = encryptor.update(padded) + encryptor.finalize()

        mac = hmac.new(hmac_key, iv + ciphertext, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(iv + ciphertext + mac).decode()

    def decrypt(self, key: bytes, token: str) -> bytes:
        try:
            aes_key, hmac_key = key[:32], key[32:]
            raw = base64.urlsafe_b64decode(token)
            iv, ciphertext, mac = raw[:16], raw[16:-32], raw[-32:]

            expected = hmac.new(hmac_key, iv + ciphertext, hashlib.sha256).digest()
            if not hmac.compare_digest(mac, expected):
                raise ValueError("HMAC verification failed")

            decryptor = Cipher(algorithms.AES(aes_key), modes.CBC(iv)).decryptor()
            padded = decryptor.update(ciphertext) + decryptor.finalize()

            unpadder = padding.PKCS7(128).unpadder()
            return unpadder.update(padded) + unpadder.finalize()
        except ValueError:
            raise
        except Exception:
            raise ValueError("Decryption failed")
