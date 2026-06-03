import sqlite3

import numpy as np

from src.db import init_db
from src.embedding import pack_vector
from src.profile import update_profile_from_feedback, update_source_stats_from_feedback
from src.utils import utc_now_iso


def _seed(conn):
    now = utc_now_iso()
    conn.execute("INSERT INTO interest_profile (profile_name, description, weight, embedding, updated_at) VALUES (?, ?, ?, ?, ?)", ("test", "test", 1.0, pack_vector(np.array([1.0, 0.0], dtype=np.float32)), now))
    conn.execute("INSERT INTO articles (title, url, fetched_at, embedding, created_at) VALUES (?, ?, ?, ?, ?)", ("positive", "https://example.com/p", now, pack_vector(np.array([0.0, 1.0], dtype=np.float32)), now))
    conn.execute("INSERT INTO articles (title, url, fetched_at, embedding, created_at) VALUES (?, ?, ?, ?, ?)", ("negative", "https://example.com/n", now, pack_vector(np.array([1.0, 0.0], dtype=np.float32)), now))
    conn.execute("INSERT INTO feedback (article_id, rating, created_at) VALUES (1, 3, ?)", (now,))
    conn.execute("INSERT INTO feedback (article_id, rating, created_at) VALUES (2, 0, ?)", (now,))
    conn.commit()


def test_feedback_updates_profile_vector(monkeypatch, tmp_path):
    db_path = tmp_path / "app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    _seed(conn)
    conn.close()
    import src.db as db_module
    import src.profile as profile_module
    monkeypatch.setattr(profile_module, "connect", lambda: db_module.connect(db_path))
    assert update_profile_from_feedback() == 1


def test_no_feedback_does_not_error(monkeypatch, tmp_path):
    db_path = tmp_path / "app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    now = utc_now_iso()
    conn.execute("INSERT INTO interest_profile (profile_name, description, weight, embedding, updated_at) VALUES (?, ?, ?, ?, ?)", ("test", "test", 1.0, pack_vector(np.array([1.0, 0.0], dtype=np.float32)), now))
    conn.commit()
    conn.close()
    import src.db as db_module
    import src.profile as profile_module
    monkeypatch.setattr(profile_module, "connect", lambda: db_module.connect(db_path))
    assert update_profile_from_feedback() == 0


def test_feedback_updates_source_stats(tmp_path):
    db_path = tmp_path / "app.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    now = utc_now_iso()
    conn.execute(
        "INSERT INTO source_stats (source_name, total_articles, source_score, updated_at) VALUES (?, ?, ?, ?)",
        ("source-a", 2, 0.8, now),
    )
    conn.execute(
        "INSERT INTO articles (source_name, title, url, fetched_at, created_at) VALUES (?, ?, ?, ?, ?)",
        ("source-a", "positive", "https://example.com/source-a/p", now, now),
    )
    conn.execute(
        "INSERT INTO articles (source_name, title, url, fetched_at, created_at) VALUES (?, ?, ?, ?, ?)",
        ("source-a", "negative", "https://example.com/source-a/n", now, now),
    )
    conn.execute("INSERT INTO feedback (article_id, rating, created_at) VALUES (1, 3, ?)", (now,))
    conn.execute("INSERT INTO feedback (article_id, rating, created_at) VALUES (2, 0, ?)", (now,))
    conn.commit()

    assert update_source_stats_from_feedback(conn) == 1
    row = conn.execute("SELECT positive_feedback_count, negative_feedback_count, source_score FROM source_stats WHERE source_name = ?", ("source-a",)).fetchone()
    conn.close()
    assert row["positive_feedback_count"] == 1
    assert row["negative_feedback_count"] == 1
    assert 0.0 <= row["source_score"] <= 1.0
