from __future__ import annotations

from .db import connect, fetch_all
from .embedding import embed_texts, pack_vector
from .utils import article_text


def embed_missing_articles(limit: int = 200) -> int:
    conn = connect()
    rows = fetch_all(conn, "SELECT id, title, summary FROM articles WHERE embedding IS NULL LIMIT ?", (limit,))
    if not rows:
        conn.close()
        print("[embed] embedded articles: 0")
        return 0
    vectors = embed_texts([article_text(row["title"], row["summary"]) for row in rows])
    for row, vector in zip(rows, vectors):
        conn.execute("UPDATE articles SET embedding = ? WHERE id = ?", (pack_vector(vector), row["id"]))
    conn.commit()
    conn.close()
    print(f"[embed] embedded articles: {len(rows)}")
    return len(rows)
