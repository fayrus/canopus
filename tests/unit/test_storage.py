import pytest
from cryptography.fernet import Fernet

from canopus.storage.database import DatabaseBackend
from canopus.storage.env import EnvBackend
from canopus.storage.local_file import LocalFileBackend
from canopus.storage.sqlite import SQLiteBackend


def sample_keys():
    return [Fernet.generate_key(), Fernet.generate_key()]


class TestLocalFileBackend:

    def test_save_and_load(self, tmp_path):
        backend = LocalFileBackend(str(tmp_path / "keys.txt"))
        keys = sample_keys()
        backend.save(keys)
        assert backend.load() == keys

    def test_load_empty_when_file_missing(self, tmp_path):
        backend = LocalFileBackend(str(tmp_path / "missing.txt"))
        assert backend.load() == []

    def test_save_multiple_keys(self, tmp_path):
        backend = LocalFileBackend(str(tmp_path / "keys.txt"))
        keys = [Fernet.generate_key() for _ in range(5)]
        backend.save(keys)
        assert backend.load() == keys

    def test_is_not_readonly(self, tmp_path):
        backend = LocalFileBackend(str(tmp_path / "keys.txt"))
        assert backend.readonly is False


class TestSQLiteBackend:

    def test_save_and_load(self, tmp_path):
        backend = SQLiteBackend(str(tmp_path / "test.db"))
        keys = sample_keys()
        backend.save(keys)
        assert backend.load() == keys

    def test_load_empty_on_new_db(self, tmp_path):
        backend = SQLiteBackend(str(tmp_path / "empty.db"))
        assert backend.load() == []

    def test_save_overwrites_previous(self, tmp_path):
        backend = SQLiteBackend(str(tmp_path / "test.db"))
        old_keys = sample_keys()
        backend.save(old_keys)
        new_keys = [Fernet.generate_key()]
        backend.save(new_keys)
        assert backend.load() == new_keys

    def test_is_not_readonly(self, tmp_path):
        backend = SQLiteBackend(str(tmp_path / "test.db"))
        assert backend.readonly is False


class TestEnvBackend:

    def test_load_single_key(self, monkeypatch):
        key = Fernet.generate_key().decode()
        monkeypatch.setenv('CANOPUS_KEYS', key)
        backend = EnvBackend()
        result = backend.load()
        assert result == [key.encode()]

    def test_load_multiple_keys(self, monkeypatch):
        keys = [Fernet.generate_key().decode() for _ in range(3)]
        monkeypatch.setenv('CANOPUS_KEYS', ','.join(keys))
        backend = EnvBackend()
        result = backend.load()
        assert result == [k.encode() for k in keys]

    def test_load_raises_when_env_missing(self, monkeypatch):
        monkeypatch.delenv('CANOPUS_KEYS', raising=False)
        with pytest.raises(ValueError, match="CANOPUS_KEYS"):
            EnvBackend().load()

    def test_save_raises_not_implemented(self, monkeypatch):
        monkeypatch.setenv('CANOPUS_KEYS', Fernet.generate_key().decode())
        with pytest.raises(NotImplementedError):
            EnvBackend().save([Fernet.generate_key()])

    def test_is_readonly(self):
        assert EnvBackend.readonly is True


class TestDatabaseBackend:

    def test_save_and_load(self, tmp_path):
        backend = DatabaseBackend(f"sqlite:///{tmp_path}/test.db")
        keys = sample_keys()
        backend.save(keys)
        assert backend.load() == keys

    def test_load_empty_on_new_db(self, tmp_path):
        backend = DatabaseBackend(f"sqlite:///{tmp_path}/empty.db")
        assert backend.load() == []

    def test_save_overwrites_previous(self, tmp_path):
        backend = DatabaseBackend(f"sqlite:///{tmp_path}/test.db")
        backend.save(sample_keys())
        new_keys = [Fernet.generate_key()]
        backend.save(new_keys)
        assert backend.load() == new_keys

    def test_is_not_readonly(self, tmp_path):
        backend = DatabaseBackend(f"sqlite:///{tmp_path}/test.db")
        assert backend.readonly is False
