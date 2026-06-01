import pytest
from cryptography.fernet import Fernet

from canopus.cipher.fernet import FernetCipher
from canopus.storage.env import EnvBackend
from canopus.storage.local_file import LocalFileBackend
from tests.conftest import _build_app


@pytest.fixture
def client(tmp_path):
    app = _build_app(
        LocalFileBackend(str(tmp_path / "keys.txt")),
        FernetCipher()
    )
    app.config['TESTING'] = True
    return app.test_client()


def encrypt(client, payload, **kwargs):
    return client.post('/encrypt', json=payload, **kwargs)


def decrypt(client, ciphertext):
    return client.post('/decrypt', json={'ciphertext': ciphertext})


class TestEncryptEndpoint:

    def test_encrypt_string(self, client):
        r = encrypt(client, {'plaintext': 'hello'})
        assert r.status_code == 200
        data = r.get_json()
        assert data['status'] == 'success'
        assert data['data']['ciphertext'].startswith('canopus:v0:f:')

    def test_encrypt_dict(self, client):
        r = encrypt(client, {'plaintext': {'user': 'waldo'}})
        assert r.status_code == 200

    def test_encrypt_missing_plaintext_returns_400(self, client):
        r = encrypt(client, {})
        assert r.status_code == 400
        assert r.get_json()['data']['code'] == 'MISSING_FIELD'

    def test_encrypt_non_json_content_type_returns_4xx(self, client):
        r = client.post('/encrypt', data='not json', content_type='text/plain')
        assert r.status_code in (400, 415)

    def test_encrypt_unsupported_type_returns_422(self, client):
        r = encrypt(client, {'plaintext': 3.14})
        assert r.status_code == 422
        assert r.get_json()['data']['code'] == 'UNSUPPORTED_TYPE'

    def test_encrypt_invalid_key_version_returns_400(self, client):
        r = encrypt(client, {'plaintext': 'hello', 'key_version': 99})
        assert r.status_code == 400
        assert r.get_json()['data']['code'] == 'INVALID_KEY_VERSION'

    def test_encrypt_invalid_key_version_type_returns_400(self, client):
        r = encrypt(client, {'plaintext': 'hello', 'key_version': 'latest'})
        assert r.status_code == 400
        assert r.get_json()['data']['code'] == 'INVALID_KEY_VERSION'

    def test_encrypt_internal_error_does_not_expose_details(self, client, monkeypatch):
        def raise_internal_error():
            raise RuntimeError('sensitive backend detail')

        monkeypatch.setattr('canopus.core.crypto.get_keys', raise_internal_error)

        r = encrypt(client, {'plaintext': 'hello'})

        assert r.status_code == 500
        data = r.get_json()
        assert data['data']['code'] == 'INTERNAL_ERROR'
        assert data['data']['message'] == 'Internal server error'


class TestDecryptEndpoint:

    def test_decrypt_success(self, client):
        ct = encrypt(client, {'plaintext': 'hello'}).get_json()['data']['ciphertext']
        r = decrypt(client, ct)
        assert r.status_code == 200
        assert r.get_json()['data']['plaintext'] == 'hello'

    def test_decrypt_dict_roundtrip(self, client):
        payload = {'user': 'waldo', 'role': 'admin'}
        ct = encrypt(client, {'plaintext': payload}).get_json()['data']['ciphertext']
        r = decrypt(client, ct)
        assert r.status_code == 200
        assert r.get_json()['data']['plaintext'] == payload

    def test_decrypt_missing_ciphertext_returns_400(self, client):
        r = client.post('/decrypt', json={})
        assert r.status_code == 400
        assert r.get_json()['data']['code'] == 'MISSING_FIELD'

    def test_decrypt_invalid_ciphertext_returns_400(self, client):
        r = decrypt(client, 'canopus:v0:f:invalidtoken')
        assert r.status_code == 400
        assert r.get_json()['data']['code'] == 'INVALID_CIPHERTEXT'

    def test_decrypt_bad_format_returns_400(self, client):
        r = decrypt(client, 'not-a-ciphertext')
        assert r.status_code == 400

    def test_decrypt_legacy_format(self, client):
        ct = encrypt(client, {'plaintext': 'legacy'}).get_json()['data']['ciphertext']
        parts = ct.split(':', 3)
        legacy = f"{parts[0]}:{parts[1]}:{parts[3]}"
        r = decrypt(client, legacy)
        assert r.status_code == 200
        assert r.get_json()['data']['plaintext'] == 'legacy'


class TestAuthentication:

    def test_no_auth_when_api_key_not_configured(self, client, monkeypatch):
        monkeypatch.setattr('canopus.config.Config.API_KEY', '')
        r = encrypt(client, {'plaintext': 'hello'})
        assert r.status_code == 200

    def test_missing_token_returns_401(self, client, monkeypatch):
        monkeypatch.setattr('canopus.config.Config.API_KEY', 'secret-key')
        r = encrypt(client, {'plaintext': 'hello'})
        assert r.status_code == 401
        assert r.get_json()['data']['code'] == 'UNAUTHORIZED'

    def test_invalid_token_returns_401(self, client, monkeypatch):
        monkeypatch.setattr('canopus.config.Config.API_KEY', 'secret-key')
        r = encrypt(client, {'plaintext': 'hello'}, headers={'X-Canopus-Token': 'wrong-key'})
        assert r.status_code == 401

    def test_valid_token_succeeds(self, client, monkeypatch):
        monkeypatch.setattr('canopus.config.Config.API_KEY', 'secret-key')
        r = encrypt(client, {'plaintext': 'hello'}, headers={'X-Canopus-Token': 'secret-key'})
        assert r.status_code == 200

    def test_auth_applies_to_decrypt(self, client, monkeypatch):
        monkeypatch.setattr('canopus.config.Config.API_KEY', 'secret-key')
        r = client.post('/decrypt', json={'ciphertext': 'canopus:v0:f:token'})
        assert r.status_code == 401

    def test_auth_applies_to_rotate_key(self, client, monkeypatch):
        monkeypatch.setattr('canopus.config.Config.API_KEY', 'secret-key')
        r = client.post('/rotate-key')
        assert r.status_code == 401


class TestRotateKeyEndpoint:

    def test_rotate_increments_version(self, client):
        r = client.post('/rotate-key')
        assert r.status_code == 200
        data = r.get_json()
        assert data['status'] == 'success'
        assert data['data']['key_version'] == 1

    def test_encrypt_uses_new_version_after_rotate(self, client):
        client.post('/rotate-key')
        ct = encrypt(client, {'plaintext': 'after rotate'}).get_json()['data']['ciphertext']
        assert ':v1:' in ct

    def test_old_ciphertext_still_decryptable_after_rotate(self, client):
        ct = encrypt(client, {'plaintext': 'before rotate'}).get_json()['data']['ciphertext']
        client.post('/rotate-key')
        r = decrypt(client, ct)
        assert r.status_code == 200
        assert r.get_json()['data']['plaintext'] == 'before rotate'

    def test_rotate_readonly_backend_returns_501(self, tmp_path, monkeypatch):
        monkeypatch.setenv('CANOPUS_KEYS', Fernet.generate_key().decode())
        app = _build_app(EnvBackend(), FernetCipher())
        app.config['TESTING'] = True
        r = app.test_client().post('/rotate-key')
        assert r.status_code == 501
        assert r.get_json()['data']['code'] == 'ROTATION_NOT_SUPPORTED'
