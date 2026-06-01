import json

from canopus.cipher.aes256cbc import AES256CBCCipher
from canopus.cipher.aes256gcm import AES256GCMCipher
from canopus.cipher.base import CipherBackend
from canopus.cipher.fernet import FernetCipher
from canopus.core.keys import get_keys

_cipher: CipherBackend | None = None
_INTERNAL_ERROR_MESSAGE = 'Internal server error'
_CIPHER_CLASSES: dict[str, type[CipherBackend]] = {
    'f': FernetCipher,
    'g': AES256GCMCipher,
    'c': AES256CBCCipher,
}


def init_cipher(cipher: CipherBackend) -> None:
    global _cipher
    _cipher = cipher


def _parse_ciphertext(ciphertext: str) -> tuple[int, str, str] | None:
    """
    Parses a canopus ciphertext and returns (version, cipher_alias, token).
    Supports both formats:
      - New: canopus:v{n}:{alias}:{token}
      - Legacy (pre-cipher abstraction): canopus:v{n}:{token}  → alias defaults to 'f'
    """
    if not ciphertext or not ciphertext.startswith('canopus:'):
        return None
    parts = ciphertext.split(':', 3)
    try:
        if len(parts) == 4:
            return int(parts[1][1:]), parts[2], parts[3]
        if len(parts) == 3:
            return int(parts[1][1:]), 'f', parts[2]
    except (ValueError, IndexError):
        return None
    return None


def _get_cipher_for(alias: str) -> CipherBackend:
    if alias not in _CIPHER_CLASSES:
        raise ValueError(f"Unknown cipher alias '{alias}'")
    return _CIPHER_CLASSES[alias]()


def _error(message: str, code: str) -> dict:
    return {'status': 'error', 'data': {'message': message, 'code': code}}


def _success(data: dict) -> dict:
    return {'status': 'success', 'data': data}


def encrypt_data(data: dict, key_version: int | None = None) -> dict:
    try:
        keys = get_keys()

        if key_version is not None and (key_version < 0 or key_version >= len(keys)):
            return _error('Invalid key version', 'INVALID_KEY_VERSION')

        if 'plaintext' not in data:
            return _error('Missing "plaintext" key in request body', 'MISSING_FIELD')

        plaintext = data['plaintext']
        if not isinstance(plaintext, (str, int, dict, list)):
            return _error('Unsupported type for "plaintext" value', 'UNSUPPORTED_TYPE')

        key = keys[key_version] if key_version is not None else keys[-1]
        key_index = key_version if key_version is not None else len(keys) - 1

        raw = json.dumps(plaintext, ensure_ascii=False).encode()
        token = _cipher.encrypt(key, raw)
        ciphertext = f"canopus:v{key_index}:{_cipher.alias}:{token}"

        return _success({'ciphertext': ciphertext})
    except Exception:
        return _error(_INTERNAL_ERROR_MESSAGE, 'INTERNAL_ERROR')


def decrypt_data(formatted_ciphertext: str) -> dict:
    parsed = _parse_ciphertext(formatted_ciphertext)
    if parsed is None:
        return _error('Invalid ciphertext format', 'INVALID_CIPHERTEXT')

    version, alias, token = parsed
    keys = get_keys()

    if version < 0 or version >= len(keys):
        return _error('Invalid ciphertext or key version', 'INVALID_CIPHERTEXT')

    try:
        cipher = _get_cipher_for(alias)
        raw = cipher.decrypt(keys[version], token)
        decoded = raw.decode()

        try:
            plaintext = json.loads(decoded)
        except json.JSONDecodeError:
            plaintext = decoded

        return _success({'plaintext': plaintext})
    except ValueError:
        return _error('Invalid ciphertext', 'INVALID_CIPHERTEXT')
    except Exception:
        return _error(_INTERNAL_ERROR_MESSAGE, 'INTERNAL_ERROR')
