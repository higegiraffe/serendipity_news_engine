from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from .utils import DB_PATH, DATA_DIR, utc_now_iso

SCHEMA = """
CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT,
    source_category TEXT,
    title TEXT NOT NULL,
    summary TEXT,
    url TEXT UNIQUE NOT NULL,
    published_at TEXT,
    fetched_at TEXT NOT NULL,
    content_hash TEXT,
    embedding BLOB,
    interest_score REAL,
    novelty_score REAL,
    source_score REAL,
    freshness_score REAL,
    final_score REAL,
    recommendation_type TEXT,
    recommendation_reason TEXT,
    generated_search_terms TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id INTEGER NOT NULL,
    rating INTEGER NOT NULL,
    feedback_label TEXT,
    comment TEXT,
    read_later INTEGER DEFAULT 0,
    deep_dive INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY(article_id) REFERENCES articles(id)
);
CREATE TABLE IF NOT EXISTS interest_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_name TEXT,
    description TEXT,
    weight REAL,
    embedding BLOB,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS source_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT UNIQUE,
    total_articles INTEGER DEFAULT 0,
    positive_feedback_count INTEGER DEFAULT 0,
    negative_feedback_count INTEGER DEFAULT 0,
    source_score REAL DEFAULT 0.5,
    updated_at TEXT NOT NULL
);
"""


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection | None = None) -> None:
    own = conn is None
    conn = conn or connect()
    conn.executescript(SCHEMA)
    conn.commit()
    if own:
        conn.close()


def save_article(conn: sqlite3.Connection, article: dict) -> bool:
    now = utc_now_iso()
    try:
        conn.execute(
            """
            INSERT INTO articles (source_name, source_category, title, summary, url, published_at, fetched_at, content_hash, source_score, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (article.get("source_name"), article.get("source_category"), article["title"], article.get("summary"), article["url"], article.get("published_at"), now, article.get("content_hash"), article.get("source_score", 0.5), now),
        )
        conn.execute(
            """
            INSERT INTO source_stats (source_name, total_articles, source_score, updated_at)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(source_name) DO UPDATE SET total_articles = total_articles + 1, updated_at = excluded.updated_at
            """,
            (article.get("source_name"), article.get("source_score", 0.5), now),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def fetch_all(conn: sqlite3.Connection, sql: str, params: Iterable = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, tuple(params)).fetchall())


def save_feedback(conn: sqlite3.Connection, article_id: int, rating: int, feedback_label: str = "", comment: str = "", read_later: bool = False, deep_dive: bool = False) -> None:
    conn.execute(
        """
        INSERT INTO feedback (article_id, rating, feedback_label, comment, read_later, deep_dive, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (article_id, rating, feedback_label, comment, int(read_later), int(deep_dive), utc_now_iso()),
    )
    conn.commit()
