from abc import ABC, abstractmethod


class CipherBackend(ABC):
    alias: str  # single char, embedded in every ciphertext

    @abstractmethod
    def generate_key(self) -> bytes:
        """Generate raw key bytes appropriate for this cipher."""

    @abstractmethod
    def encrypt(self, key: bytes, data: bytes) -> str:
        """Encrypt data and return an encoded token string."""

    @abstractmethod
    def decrypt(self, key: bytes, token: str) -> bytes:
        """Decrypt token and return plaintext bytes."""
