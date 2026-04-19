import pytest

from canopus.cipher.aes256cbc import AES256CBCCipher
from canopus.cipher.aes256gcm import AES256GCMCipher
from canopus.cipher.fernet import FernetCipher
from canopus.core import crypto, keys
from canopus.storage.local_file import LocalFileBackend


@pytest.fixture(params=[FernetCipher, AES256GCMCipher, AES256CBCCipher])
def cipher(request):
    return request.param()


@pytest.fixture
def cipher_f():
    return FernetCipher()


@pytest.fixture
def cipher_g():
    return AES256GCMCipher()


@pytest.fixture
def cipher_c():
    return AES256CBCCipher()


@pytest.fixture
def file_backend(tmp_path):
    return LocalFileBackend(str(tmp_path / "keys.txt"))


@pytest.fixture
def app_with(tmp_path):
    """Factory fixture — returns a Flask test client configured with a given cipher."""
    def _make(cipher_instance=None):
        from canopus.api import create_app
        from canopus.storage.local_file import LocalFileBackend

        if cipher_instance is None:
            cipher_instance = FernetCipher()

        backend = LocalFileBackend(str(tmp_path / f"keys_{cipher_instance.alias}.txt"))
        if hasattr(create_app, '__wrapped__'):
            app = create_app.__wrapped__(backend, cipher_instance)
        else:
            app = _build_app(backend, cipher_instance)
        app.config['TESTING'] = True
        return app.test_client()

    return _make


def _build_app(backend, cipher_instance):
    from flask import Flask

    from canopus.api.routes import bp

    app = Flask(__name__)
    keys.init(backend, cipher_instance)
    crypto.init_cipher(cipher_instance)
    app.register_blueprint(bp)
    return app


@pytest.fixture
def client(tmp_path):
    app = _build_app(
        LocalFileBackend(str(tmp_path / "keys.txt")),
        FernetCipher()
    )
    app.config['TESTING'] = True
    return app.test_client()
