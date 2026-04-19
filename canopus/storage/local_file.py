import base64
import os

from canopus.storage.base import KeyStorageBackend


class LocalFileBackend(KeyStorageBackend):

    def __init__(self, path: str):
        self.path = path

    def load(self) -> list[bytes]:
        if not os.path.exists(self.path):
            return []
        with open(self.path, 'rb') as f:
            return [base64.b64decode(line.strip()) for line in f if line.strip()]

    def save(self, keys: list[bytes]) -> None:
        with open(self.path, 'wb') as f:
            for key in keys:
                f.write(base64.b64encode(key) + b'\n')
