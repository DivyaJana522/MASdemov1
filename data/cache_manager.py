from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from typing import Any, Optional

from ..utils.logging_utils import get_logger


class CacheManager:
    """SQLite-backed JSON cache with TTL support, safe for multi-threaded reads.

    Stores small JSON-serializable payloads keyed by strings. Use for API responses
    and computed snapshots to reduce provider calls and improve resilience.
    """

    def __init__(self, db_path: str, default_ttl: int = 3600) -> None:
        self.db_path = db_path
        self.default_ttl = default_ttl
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._lock = threading.RLock()
        self._logger = get_logger(__name__)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (\n"
            "  key TEXT PRIMARY KEY,\n"
            "  value TEXT NOT NULL,\n"
            "  expiry INTEGER NOT NULL\n"
            ")"
        )
        self._conn.commit()

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        ttl = self.default_ttl if ttl is None else ttl
        expiry = int(time.time()) + int(ttl)
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            self._conn.execute(
                "INSERT INTO cache(key, value, expiry) VALUES(?,?,?)\n"
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, expiry=excluded.expiry",
                (key, payload, expiry),
            )
            self._conn.commit()

    def get(self, key: str, allow_stale: bool = False) -> Optional[Any]:
        """Get cached value. If allow_stale=True, returns expired cache instead of None."""
        now = int(time.time())
        with self._lock:
            cur = self._conn.execute("SELECT value, expiry FROM cache WHERE key=?", (key,))
            row = cur.fetchone()
        if not row:
            return None
        value_str, expiry = row
        if expiry < now:
            if allow_stale:
                # Return stale cache when allowed (useful for rate limiting fallback)
                self._logger.info("Returning stale cache for key %s", key)
                try:
                    return json.loads(value_str)
                except Exception as e:
                    self._logger.warning("Failed to decode stale cache for key %s: %s", key, e)
                    return None
            else:
                # Lazy expiration cleanup
                try:
                    with self._lock:
                        self._conn.execute("DELETE FROM cache WHERE key=?", (key,))
                        self._conn.commit()
                except Exception:
                    pass
                return None
        try:
            return json.loads(value_str)
        except Exception as e:
            self._logger.warning("Failed to decode cache for key %s: %s", key, e)
            return None

    def purge_expired(self) -> int:
        now = int(time.time())
        with self._lock:
            cur = self._conn.execute("DELETE FROM cache WHERE expiry<?", (now,))
            self._conn.commit()
            return cur.rowcount

    def close(self) -> None:
        try:
            with self._lock:
                self._conn.close()
        except Exception:
            pass
