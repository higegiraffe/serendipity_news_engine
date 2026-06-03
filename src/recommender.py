from __future__ import annotations

from .db import connect, fetch_all
from .embedding import unpack_vector
from .profile import interest_score, profile_vectors
from .scoring import final_score, freshness_score, novelty_score
from .utils import load_settings


def classify_recommendation(interest: float, novelty: float, source: float) -> str:
    if interest >= 0.72:
        return "known_interest"
    if interest >= 0.48 and novelty >= 0.35:
        return "adjacent_interest"
    if interest >= 0.25 and novelty >= 0.55 and source >= 0.55:
        return "surprise"
    return "general"


def reason_for(kind: str, matched_profile: str, interest: float, novelty: float) -> str:
    if kind == "known_interest":
        return f"Close to your interest profile '{matched_profile}' (interest={interest:.2f})."
    if kind == "adjacent_interest":
        return f"A little away from '{matched_profile}', but novel enough to broaden the search (novelty={novelty:.2f})."
    if kind == "surprise":
        return f"Not your usual center, but it is novel and from a trusted enough source (novelty={novelty:.2f})."
    return "Included by overall score."


def search_terms(title: str, summary: str | None, matched_profile: str) -> str:
    words = [word.strip(".,:;()[]{}'\"") for word in f"{title} {summary or ''}".split()]
    keywords: list[str] = []
    lowered: set[str] = set()
    for word in words:
        if len(word) >= 4 and word.lower() not in lowered:
            keywords.append(word)
            lowered.add(word.lower())
        if len(keywords) >= 5:
            break
    if matched_profile:
        keywords.append(matched_profile)
    return " ".join(keywords[:8])


def score_articles() -> int:
    settings = load_settings()
    weights = settings.get("scoring", {})
    conn = connect()
    profiles = profile_vectors(conn)
    seen = [unpack_vector(row["embedding"]) for row in fetch_all(conn, "SELECT a.embedding FROM articles a JOIN feedback f ON f.article_id = a.id WHERE a.embedding IS NOT NULL")]
    rows = fetch_all(conn, "SELECT * FROM articles WHERE embedding IS NOT NULL")
    count = 0
    for row in rows:
        vector = unpack_vector(row["embedding"])
        interest, matched_profile = interest_score(vector, profiles)
        novelty = novelty_score(vector, seen)
        freshness = freshness_score(row["published_at"])
        source = row["source_score"] if row["source_score"] is not None else 0.5
        score = final_score(interest, novelty, freshness, source, weights)
        kind = classify_recommendation(interest, novelty, source)
        conn.execute("""
            UPDATE articles SET interest_score = ?, novelty_score = ?, freshness_score = ?, source_score = ?, final_score = ?, recommendation_type = ?, recommendation_reason = ?, generated_search_terms = ?
            WHERE id = ?
        """, (interest, novelty, freshness, source, score, kind, reason_for(kind, matched_profile, interest, novelty), search_terms(row["title"], row["summary"], matched_profile), row["id"]))
        count += 1
    conn.commit()
    conn.close()
    print(f"[score] scored articles: {count}")
    return count


def recommendations(limit: int | None = None) -> list[dict]:
    settings = load_settings()
    limit = limit or settings.get("app", {}).get("recommendation_count", 30)
    conn = connect()
    rows = fetch_all(conn, "SELECT * FROM articles WHERE final_score IS NOT NULL ORDER BY final_score DESC, published_at DESC LIMIT ?", (limit,))
    conn.close()
    return [dict(row) for row in rows]
