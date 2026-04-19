from canopus.cipher.base import CipherBackend
from canopus.storage.base import KeyStorageBackend

_backend: KeyStorageBackend | None = None
_cipher: CipherBackend | None = None
_keys: list[bytes] = []


def init(backend: KeyStorageBackend, cipher: CipherBackend) -> None:
    global _backend, _cipher, _keys
    _backend = backend
    _cipher = cipher
    _keys = backend.load()
    if not _keys:
        _keys = [cipher.generate_key()]
        _backend.save(_keys)


def get_keys() -> list[bytes]:
    return _keys


def rotate_key() -> None:
    if _backend.readonly:
        raise NotImplementedError("The active storage backend does not support key rotation.")
    new_key = _cipher.generate_key()
    _keys.append(new_key)
    _backend.save(_keys)


def load_keys() -> list[bytes]:
    return _keys
