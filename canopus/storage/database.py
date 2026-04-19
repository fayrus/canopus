import base64

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    delete,
    func,
    insert,
    select,
)

from canopus.storage.base import KeyStorageBackend


class DatabaseBackend(KeyStorageBackend):
    """
    RDBMS backend powered by SQLAlchemy.

    Supports any SQLAlchemy-compatible database via a connection URL:
      - PostgreSQL:  postgresql://user:pass@host/dbname
      - MySQL:       mysql+pymysql://user:pass@host/dbname
      - SQLite:      sqlite:///path/to/canopus.db

    Requires the appropriate DB driver to be installed separately:
      - PostgreSQL:  pip install psycopg2-binary
      - MySQL:       pip install pymysql
    """

    def __init__(self, url: str):
        self._engine = create_engine(url)
        self._meta = MetaData()
        self._table = Table(
            'canopus_keys', self._meta,
            Column('version', Integer, primary_key=True, autoincrement=True),
            Column('key_data', Text, nullable=False),
            Column('created_at', DateTime, server_default=func.now()),
        )
        self._meta.create_all(self._engine)

    def load(self) -> list[bytes]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(self._table.c.key_data).order_by(self._table.c.version)
            ).fetchall()
        return [base64.b64decode(row[0]) for row in rows]

    def save(self, keys: list[bytes]) -> None:
        with self._engine.begin() as conn:
            conn.execute(delete(self._table))
            if keys:
                conn.execute(
                    insert(self._table),
                    [{'key_data': base64.b64encode(key).decode()} for key in keys]
                )
