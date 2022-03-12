import pickle
import sqlite3
from . import logger
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple


class Storage():
    def __init__(self, filename: str):
        self._filename = filename
        self._conn: Optional[sqlite3.Connection] = None
        self._table_name = 'objects'
        self._table_created = False
        self._greeted = False

    def __del__(self):
        self._close()

    def set(self, key: int, obj: Any) -> None:
        self._open()

        t = datetime.now()
        query = f'REPLACE INTO {self._table_name} (id, time, value) VALUES (?, ?, ?)'

        try:
            self._execute(query, [key, t, self._serialize(obj)])
        finally:
            self._close()

    def get(self, key: int) -> Any:
        self._open()

        query = f'SELECT value FROM {self._table_name} WHERE id = ?'

        try:
            cursor = self._execute(query, [key])
            row = cursor.fetchone()
        finally:
            self._close()

        if row is None:
            return None

        return self._deserialize(row[0])

    def get_all(self, reverse=False) -> List[Tuple[int, Any]]:
        """Return all item in the insertion order.

        The most recently inserted or updated item is last. If reverse is True,
        the most recently inserted is first.
        """
        self._open()

        ordering = 'DESC' if reverse else 'ASC'
        query = f'SELECT id, value FROM {self._table_name} ORDER BY time {ordering}'

        try:
            cursor = self._execute(query)
            return [(x[0], self._deserialize(x[1])) for x in cursor]
        finally:
            self._close()

    def delete(self, key: int) -> None:
        self._open()

        query = f'DELETE FROM {self._table_name} WHERE id = ?'

        try:
            self._execute(query, [key])
        finally:
            self._close()

    def _open(self) -> None:
        if self._conn is None:
            if self._filename != ':memory:':
                Path(self._filename).parent.mkdir(parents=True, exist_ok=True)

            self._conn = sqlite3.connect(
                self._filename,
                timeout=1,
                isolation_level=None,
                check_same_thread=False
            )

            if not self._greeted:
                self._greeted = True
                self._log_version()

            cursor = self._conn.cursor()
            cursor.execute('PRAGMA journal_mode=MEMORY')
            cursor.close()

            self._create_table()

    def _close(self) -> None:
        if self._conn is not None:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def _create_table(self) -> None:
        if not self._table_created:
            self._execute(f'CREATE TABLE IF NOT EXISTS {self._table_name} '
                          '(id INTEGER PRIMARY KEY, time TIMESTAMP, value BLOB)')
            self._table_created = True

    def _log_version(self) -> None:
        cursor = self._execute('SELECT SQLITE_VERSION()')
        sqlite_version = cursor.fetchone()[0]
        logger.info(
            f'Successfully connected to {self._filename} '
            f'(SQLite version {sqlite_version})'
        )

    def _execute(self, query: str, params: Optional[Sequence[Any]] = None) -> sqlite3.Cursor:
        if self._conn is None:
            raise RuntimeError('Not connected')

        cursor = self._conn.cursor()
        if params is not None:
            return cursor.execute(query, params)
        else:
            return cursor.execute(query)

    def _serialize(self, obj: Any) -> bytes:
        return pickle.dumps(obj, protocol=4)

    def _deserialize(self, serialized: bytes) -> Any:
        return pickle.loads(serialized)
