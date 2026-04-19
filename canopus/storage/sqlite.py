import base64
import sqlite3

from canopus.storage.base import KeyStorageBackend


class SQLiteBackend(KeyStorageBackend):

    def __init__(self, path: str):
        self.path = path
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS canopus_keys (
                    version     INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_data    TEXT NOT NULL,
                    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def load(self) -> list[bytes]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT key_data FROM canopus_keys ORDER BY version ASC"
            ).fetchall()
        return [base64.b64decode(row[0]) for row in rows]

    def save(self, keys: list[bytes]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM canopus_keys")
            conn.executemany(
                "INSERT INTO canopus_keys (key_data) VALUES (?)",
                [(base64.b64encode(key).decode(),) for key in keys]
            )
