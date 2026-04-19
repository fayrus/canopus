import os

from canopus.storage.base import KeyStorageBackend

_ENV_VAR = 'CANOPUS_KEYS'


class EnvBackend(KeyStorageBackend):
    """
    Read-only backend that loads keys from the CANOPUS_KEYS environment variable.

    Format: comma-separated base64-encoded Fernet keys.
    Example:
        CANOPUS_KEYS="key1base64==,key2base64=="

    Key rotation is not supported — env vars cannot be persisted at runtime.
    """
    readonly = True

    def load(self) -> list[bytes]:
        raw = os.getenv(_ENV_VAR, '').strip()
        if not raw:
            raise ValueError(
                f"'{_ENV_VAR}' environment variable is not set or empty. "
                "Provide at least one Fernet key in base64 format."
            )
        return [k.strip().encode() for k in raw.split(',') if k.strip()]

    def save(self, keys: list[bytes]) -> None:
        raise NotImplementedError("EnvBackend is read-only. Key rotation is not supported.")
