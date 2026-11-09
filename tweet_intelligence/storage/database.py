"""SQLite storage for words, POS tags, and sentence structure patterns."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Iterable


DEFAULT_DB_PATH = Path(
    os.environ.get("TWEET_INTELLIGENCE_DB", "data/tweet_intelligence.db")
)


class Storage:
    """Persist words and sentence structures for efficient retrieval."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        if str(self.db_path) != ":memory:":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS words (
                word TEXT NOT NULL,
                pos  TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 1,
                PRIMARY KEY (word, pos)
            );

            CREATE TABLE IF NOT EXISTS structures (
                pattern TEXT PRIMARY KEY,
                count INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS tweets (
                id TEXT PRIMARY KEY,
                author TEXT,
                text TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'live'
            );

            CREATE INDEX IF NOT EXISTS idx_words_pos ON words(pos);
            CREATE INDEX IF NOT EXISTS idx_words_count ON words(count DESC);
            CREATE INDEX IF NOT EXISTS idx_structures_count ON structures(count DESC);
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> Storage:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def save_tweet(
        self,
        tweet_id: str,
        text: str,
        author: str | None = None,
        source: str = "live",
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO tweets (id, author, text, source)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                text = excluded.text,
                author = COALESCE(excluded.author, tweets.author),
                source = excluded.source
            """,
            (tweet_id, author, text, source),
        )
        self._conn.commit()

    def record_word(self, word: str, pos: str) -> None:
        word = word.lower().strip()
        if not word:
            return
        self._conn.execute(
            """
            INSERT INTO words (word, pos, count) VALUES (?, ?, 1)
            ON CONFLICT(word, pos) DO UPDATE SET count = count + 1
            """,
            (word, pos),
        )
        self._conn.commit()

    def record_words(self, tokens: Iterable[tuple[str, str]]) -> None:
        for word, pos in tokens:
            word = word.lower().strip()
            if not word:
                continue
            self._conn.execute(
                """
                INSERT INTO words (word, pos, count) VALUES (?, ?, 1)
                ON CONFLICT(word, pos) DO UPDATE SET count = count + 1
                """,
                (word, pos),
            )
        self._conn.commit()

    def record_structure(self, pattern: str) -> None:
        pattern = pattern.strip()
        if not pattern:
            return
        self._conn.execute(
            """
            INSERT INTO structures (pattern, count) VALUES (?, 1)
            ON CONFLICT(pattern) DO UPDATE SET count = count + 1
            """,
            (pattern,),
        )
        self._conn.commit()

    def get_words_by_pos(self, pos: str, limit: int = 50) -> list[tuple[str, int]]:
        """Indexed POS lookup (idx_words_pos) ordered by frequency for generation."""
        rows = self._conn.execute(
            """
            SELECT word, count FROM words
            WHERE pos = ?
            ORDER BY count DESC, word ASC
            LIMIT ?
            """,
            (pos, limit),
        ).fetchall()
        return [(row["word"], row["count"]) for row in rows]

    def get_words_by_pos_prefix(
        self, pos_prefix: str, limit: int = 50
    ) -> list[tuple[str, int]]:
        """Retrieve words whose POS tag starts with ``pos_prefix`` (e.g. 'NN' → NN/NNS/NNP)."""
        rows = self._conn.execute(
            """
            SELECT word, count FROM words
            WHERE pos = ? OR pos LIKE ?
            ORDER BY count DESC, word ASC
            LIMIT ?
            """,
            (pos_prefix, f"{pos_prefix}%", limit),
        ).fetchall()
        return [(row["word"], row["count"]) for row in rows]

    def get_all_words(self, limit: int = 100) -> list[tuple[str, str, int]]:
        rows = self._conn.execute(
            """
            SELECT word, pos, count FROM words
            ORDER BY count DESC, word ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [(row["word"], row["pos"], row["count"]) for row in rows]

    def get_structures(self, limit: int = 50) -> list[tuple[str, int]]:
        """Indexed frequency lookup of sentence structures for generation."""
        rows = self._conn.execute(
            """
            SELECT pattern, count FROM structures
            ORDER BY count DESC, pattern ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [(row["pattern"], row["count"]) for row in rows]

    def index_names(self) -> list[str]:
        """Return created index names (used to verify efficient retrieval setup)."""
        rows = self._conn.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'index' AND sql IS NOT NULL
            ORDER BY name
            """
        ).fetchall()
        return [row["name"] for row in rows]

    def tweet_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM tweets").fetchone()
        return int(row["n"])

    def word_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM words").fetchone()
        return int(row["n"])

    def structure_count(self) -> int:
        row = self._conn.execute("SELECT COUNT(*) AS n FROM structures").fetchone()
        return int(row["n"])

    def clear(self) -> None:
        self._conn.executescript(
            "DELETE FROM words; DELETE FROM structures; DELETE FROM tweets;"
        )
        self._conn.commit()
