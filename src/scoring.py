from __future__ import annotations

import numpy as np


def cosine_similarity(a, b) -> float:
    if a is None or b is None or len(a) == 0 or len(b) == 0:
        return 0.0
    size = min(len(a), len(b))
    av = np.asarray(a[:size], dtype=np.float32)
    bv = np.asarray(b[:size], dtype=np.float32)
    denom = float(np.linalg.norm(av) * np.linalg.norm(bv))
    if denom == 0:
        return 0.0
    return max(0.0, min(1.0, (float(np.dot(av, bv)) + 1.0) / 2.0))


def freshness_score(published_at: str | None) -> float:
    if not published_at:
        return 0.3
    from datetime import datetime, timezone
    try:
        published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
    except Exception:
        return 0.3
    age_days = (datetime.now(timezone.utc) - published.astimezone(timezone.utc)).total_seconds() / 86400
    if age_days <= 1:
        return 1.0
    if age_days <= 3:
        return 0.8
    if age_days <= 7:
        return 0.6
    if age_days <= 30:
        return 0.3
    return 0.1


def novelty_score(article_embedding, seen_embeddings) -> float:
    if article_embedding is None or not seen_embeddings:
        return 0.7
    similarities = [cosine_similarity(article_embedding, seen) for seen in seen_embeddings if seen is not None]
    return max(0.0, min(1.0, 1.0 - max(similarities, default=0.0)))


def final_score(interest: float, novelty: float, freshness: float, source: float, weights: dict | None = None) -> float:
    weights = weights or {}
    score = float(weights.get("similarity_weight", 0.60)) * interest + float(weights.get("novelty_weight", 0.15)) * novelty + float(weights.get("freshness_weight", 0.15)) * freshness + float(weights.get("source_weight", 0.10)) * source
    return max(0.0, min(1.0, score))


def source_score(base: float, positive: int = 0, negative: int = 0) -> float:
    total = positive + negative
    if total == 0:
        return max(0.0, min(1.0, base))
    adjusted = 0.5 + (positive / total) * 0.3 - (negative / total) * 0.3
    return max(0.0, min(1.0, adjusted))
