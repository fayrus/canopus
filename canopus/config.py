import os


class Config:
    # Server
    DEBUG = os.getenv('CANOPUS_DEBUG', 'false').lower() == 'true'
    HOST = os.getenv('CANOPUS_HOST', '127.0.0.1')
    PORT = int(os.getenv('CANOPUS_PORT', '2107'))

    # Storage backend: "file" | "sqlite"
    STORAGE_BACKEND = os.getenv('CANOPUS_STORAGE_BACKEND', 'file')

    # LocalFileBackend
    KEYS_FILE = os.getenv('CANOPUS_KEYS_FILE', 'keys.txt')

    # SQLiteBackend
    SQLITE_PATH = os.getenv('CANOPUS_SQLITE_PATH', 'canopus.db')

    # DatabaseBackend (SQLAlchemy URL)
    DATABASE_URL = os.getenv('CANOPUS_DATABASE_URL', '')

    # AWSSecretsBackend
    AWS_SECRET_NAME = os.getenv('CANOPUS_AWS_SECRET_NAME', '')
    AWS_REGION = os.getenv('CANOPUS_AWS_REGION', 'us-east-1')

    # CipherBackend: "f" (Fernet) | "g" (AES-256-GCM) | "c" (AES-256-CBC)
    CIPHER = os.getenv('CANOPUS_CIPHER', 'f')

    # Authentication — leave empty to disable (development mode)
    API_KEY = os.getenv('CANOPUS_API_KEY', '')

    # Key rotation — separate key required to call /rotate-key (falls back to API_KEY if unset)
    ROTATE_KEY = os.getenv('CANOPUS_ROTATE_KEY', '')

    # Set to "false" to disable /rotate-key entirely (recommended in production)
    ROTATION_ENABLED = os.getenv('CANOPUS_ROTATION_ENABLED', 'true').lower() == 'true'


def get_storage_backend():
    from canopus.storage.env import EnvBackend
    from canopus.storage.local_file import LocalFileBackend
    from canopus.storage.sqlite import SQLiteBackend

    backends = {
        'file': lambda: LocalFileBackend(Config.KEYS_FILE),
        'sqlite': lambda: SQLiteBackend(Config.SQLITE_PATH),
        'env': lambda: EnvBackend(),
        'database': _build_database_backend,
        'aws_secrets': _build_aws_secrets_backend,
    }

    backend_name = Config.STORAGE_BACKEND
    if backend_name not in backends:
        raise ValueError(
            f"Unknown storage backend '{backend_name}'. "
            f"Valid options: {', '.join(backends.keys())}"
        )

    return backends[backend_name]()


def get_cipher_backend():
    from canopus.cipher.aes256cbc import AES256CBCCipher
    from canopus.cipher.aes256gcm import AES256GCMCipher
    from canopus.cipher.fernet import FernetCipher

    ciphers = {
        'f': FernetCipher,
        'g': AES256GCMCipher,
        'c': AES256CBCCipher,
    }

    alias = Config.CIPHER
    if alias not in ciphers:
        raise ValueError(
            f"Unknown cipher '{alias}'. Valid options: {', '.join(ciphers.keys())}"
        )
    return ciphers[alias]()


def _build_aws_secrets_backend():
    from canopus.storage.aws_secrets import AWSSecretsBackend
    if not Config.AWS_SECRET_NAME:
        raise ValueError(
            "'CANOPUS_AWS_SECRET_NAME' is required when using the aws_secrets backend."
        )
    return AWSSecretsBackend(Config.AWS_SECRET_NAME, Config.AWS_REGION)


def _build_database_backend():
    from canopus.storage.database import DatabaseBackend
    if not Config.DATABASE_URL:
        raise ValueError(
            "'CANOPUS_DATABASE_URL' is required when using the database backend. "
            "Example: postgresql://user:pass@host/dbname"
        )
    return DatabaseBackend(Config.DATABASE_URL)
