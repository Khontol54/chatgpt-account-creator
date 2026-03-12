"""
Database manager – SQLite3 backend for storing accounts and action logs.
"""

import os
import sqlite3
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.logger import get_logger

logger = get_logger("db_manager")

_lock = threading.Lock()


class DatabaseManager:
    """Thread-safe SQLite database manager."""

    def __init__(self, db_path: str = "") -> None:
        from config import config  # noqa: PLC0415

        self._db_path: str = db_path or config.DB_PATH
        self._conn: Optional[sqlite3.Connection] = None

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def initialize(self) -> None:
        """Open the database and create tables if they do not exist."""
        os.makedirs(os.path.dirname(self._db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()
        logger.info("Database initialised at %s", self._db_path)

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("Database connection closed")

    # ------------------------------------------------------------------ #
    # Schema                                                               #
    # ------------------------------------------------------------------ #

    def _create_tables(self) -> None:
        assert self._conn is not None
        with _lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    email       TEXT    NOT NULL UNIQUE,
                    password    TEXT    NOT NULL,
                    status      TEXT    NOT NULL DEFAULT 'pending',
                    verified    INTEGER NOT NULL DEFAULT 0,
                    created_at  TEXT    NOT NULL,
                    updated_at  TEXT    NOT NULL,
                    last_login  TEXT,
                    notes       TEXT
                );

                CREATE TABLE IF NOT EXISTS logs (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id  INTEGER REFERENCES accounts(id),
                    action      TEXT    NOT NULL,
                    status      TEXT    NOT NULL,
                    timestamp   TEXT    NOT NULL,
                    details     TEXT
                );
                """
            )

    # ------------------------------------------------------------------ #
    # Account helpers                                                      #
    # ------------------------------------------------------------------ #

    def _row_to_dict(self, row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
        return dict(row) if row else None

    def save_account(self, email: str, password: str, notes: str = "") -> int:
        """Insert a new account row and return its id."""
        assert self._conn is not None
        now = datetime.utcnow().isoformat()
        with _lock, self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO accounts (email, password, status, verified, created_at, updated_at, notes)
                VALUES (?, ?, 'pending', 0, ?, ?, ?)
                """,
                (email, password, now, now, notes),
            )
            account_id = cursor.lastrowid
        logger.debug("Saved account %s (id=%s)", email, account_id)
        return account_id  # type: ignore[return-value]

    def update_account_status(
        self, account_id: int, status: str, verified: bool = False
    ) -> None:
        assert self._conn is not None
        now = datetime.utcnow().isoformat()
        with _lock, self._conn:
            self._conn.execute(
                """
                UPDATE accounts
                SET status=?, verified=?, updated_at=?
                WHERE id=?
                """,
                (status, int(verified), now, account_id),
            )

    def get_account_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        assert self._conn is not None
        with _lock:
            row = self._conn.execute(
                "SELECT * FROM accounts WHERE email=?", (email,)
            ).fetchone()
        return self._row_to_dict(row)

    def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        assert self._conn is not None
        with _lock:
            row = self._conn.execute(
                "SELECT * FROM accounts WHERE id=?", (account_id,)
            ).fetchone()
        return self._row_to_dict(row)

    def get_all_accounts(self) -> List[Dict[str, Any]]:
        assert self._conn is not None
        with _lock:
            rows = self._conn.execute(
                "SELECT * FROM accounts ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Log helpers                                                          #
    # ------------------------------------------------------------------ #

    def add_log(
        self,
        action: str,
        status: str,
        account_id: Optional[int] = None,
        details: str = "",
    ) -> None:
        assert self._conn is not None
        now = datetime.utcnow().isoformat()
        with _lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO logs (account_id, action, status, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (account_id, action, status, now, details),
            )

    def get_logs(self, account_id: Optional[int] = None) -> List[Dict[str, Any]]:
        assert self._conn is not None
        with _lock:
            if account_id is not None:
                rows = self._conn.execute(
                    "SELECT * FROM logs WHERE account_id=? ORDER BY timestamp DESC",
                    (account_id,),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT * FROM logs ORDER BY timestamp DESC"
                ).fetchall()
        return [dict(r) for r in rows]


# Module-level singleton
db = DatabaseManager()
