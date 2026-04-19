from abc import ABC, abstractmethod


class KeyStorageBackend(ABC):
    readonly: bool = False

    @abstractmethod
    def load(self) -> list[bytes]:
        """Load all key versions ordered by version number."""

    @abstractmethod
    def save(self, keys: list[bytes]) -> None:
        """Persist the full list of keys."""
