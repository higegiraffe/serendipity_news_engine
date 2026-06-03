from __future__ import annotations

import numpy as np

from .db import connect, fetch_all
from .embedding import embed_texts, pack_vector, unpack_vector
from .scoring import cosine_similarity, source_score
from .utils import CONFIG_DIR, load_yaml, utc_now_iso


def init_interest_profile() -> int:
    config = load_yaml(CONFIG_DIR / "interests.yaml")
    interests = config.get("seed_interests", [])
    if not interests:
        return 0
    conn = connect()
    existing = conn.execute("SELECT COUNT(*) FROM interest_profile").fetchone()[0]
    if existing:
        conn.close()
        return 0
    texts = [f"{item.get('name', '')}\n{item.get('description', '')}" for item in interests]
    vectors = embed_texts(texts)
    for item, vector in zip(interests, vectors):
        conn.execute("INSERT INTO interest_profile (profile_name, description, weight, embedding, updated_at) VALUES (?, ?, ?, ?, ?)", (item.get("name"), item.get("description"), float(item.get("weight", 1.0)), pack_vector(vector), utc_now_iso()))
    conn.commit()
    conn.close()
    print(f"[init] interest profiles: {len(interests)}")
    return len(interests)


def profile_vectors(conn):
    rows = fetch_all(conn, "SELECT id, profile_name, description, weight, embedding FROM interest_profile")
    return [(row, unpack_vector(row["embedding"])) for row in rows]


def interest_score(article_embedding, profiles) -> tuple[float, str]:
    best_score = 0.0
    best_name = ""
    for row, vector in profiles:
        score = cosine_similarity(article_embedding, vector) * float(row["weight"] or 1.0)
        if score > best_score:
            best_score = score
            best_name = row["profile_name"]
    return max(0.0, min(1.0, best_score)), best_name


def update_source_stats_from_feedback(conn) -> int:
    rows = fetch_all(conn, "SELECT source_name, source_score FROM source_stats WHERE source_name IS NOT NULL")
    updated = 0
    for row in rows:
        positive = conn.execute(
            """
            SELECT COUNT(*)
            FROM feedback f
            JOIN articles a ON a.id = f.article_id
            WHERE a.source_name = ? AND f.rating >= 2
            """,
            (row["source_name"],),
        ).fetchone()[0]
        negative = conn.execute(
            """
            SELECT COUNT(*)
            FROM feedback f
            JOIN articles a ON a.id = f.article_id
            WHERE a.source_name = ? AND f.rating <= 1
            """,
            (row["source_name"],),
        ).fetchone()[0]
        score = source_score(float(row["source_score"] or 0.5), positive, negative)
        conn.execute(
            """
            UPDATE source_stats
            SET positive_feedback_count = ?, negative_feedback_count = ?, source_score = ?, updated_at = ?
            WHERE source_name = ?
            """,
            (positive, negative, score, utc_now_iso(), row["source_name"]),
        )
        updated += 1
    return updated


def update_profile_from_feedback() -> int:
    conn = connect()
    update_source_stats_from_feedback(conn)
    profiles = profile_vectors(conn)
    if not profiles:
        conn.commit()
        conn.close()
        return 0
    positive = [unpack_vector(row["embedding"]) for row in fetch_all(conn, "SELECT a.embedding FROM articles a JOIN feedback f ON f.article_id = a.id WHERE f.rating >= 2 AND a.embedding IS NOT NULL")]
    negative = [unpack_vector(row["embedding"]) for row in fetch_all(conn, "SELECT a.embedding FROM articles a JOIN feedback f ON f.article_id = a.id WHERE f.rating <= 1 AND a.embedding IS NOT NULL")]
    if not positive and not negative:
        conn.commit()
        conn.close()
        return 0
    pos_mean = np.mean(positive, axis=0) if positive else None
    neg_mean = np.mean(negative, axis=0) if negative else None
    updated = 0
    for row, vector in profiles:
        new_vector = vector * 0.8
        if pos_mean is not None:
            size = min(len(new_vector), len(pos_mean))
            new_vector[:size] += pos_mean[:size] * 0.3
        if neg_mean is not None:
            size = min(len(new_vector), len(neg_mean))
            new_vector[:size] -= neg_mean[:size] * 0.1
        norm = np.linalg.norm(new_vector)
        if norm:
            new_vector = new_vector / norm
        conn.execute("UPDATE interest_profile SET embedding = ?, updated_at = ? WHERE id = ?", (pack_vector(new_vector), utc_now_iso(), row["id"]))
        updated += 1
    conn.commit()
    conn.close()
    return updated
