import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from canopus.cipher.base import CipherBackend


class AES256GCMCipher(CipherBackend):
    """
    AES-256-GCM — authenticated encryption.
    Recommended for HIPAA, HITRUST, SOC2, and PCI DSS environments.
    Key size: 32 bytes. Nonce size: 12 bytes (prepended to token).
    """
    alias = 'g'

    def generate_key(self) -> bytes:
        return os.urandom(32)

    def encrypt(self, key: bytes, data: bytes) -> str:
        nonce = os.urandom(12)
        ciphertext = AESGCM(key).encrypt(nonce, data, None)
        return base64.urlsafe_b64encode(nonce + ciphertext).decode()

    def decrypt(self, key: bytes, token: str) -> bytes:
        try:
            raw = base64.urlsafe_b64decode(token)
            nonce, ciphertext = raw[:12], raw[12:]
            return AESGCM(key).decrypt(nonce, ciphertext, None)
        except Exception:
            raise ValueError("Decryption failed")
