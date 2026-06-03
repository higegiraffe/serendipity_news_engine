from datetime import datetime, timedelta, timezone

from src.recommender import classify_recommendation
from src.scoring import final_score, freshness_score


def test_freshness_score_buckets():
    now = datetime.now(timezone.utc)
    assert freshness_score(now.isoformat()) == 1.0
    assert freshness_score((now - timedelta(days=2)).isoformat()) == 0.8
    assert freshness_score((now - timedelta(days=10)).isoformat()) == 0.3
    assert freshness_score(None) == 0.3


def test_final_score_is_clipped():
    assert 0.0 <= final_score(2.0, 2.0, 2.0, 2.0) <= 1.0
    assert final_score(-1.0, -1.0, -1.0, -1.0) == 0.0


def test_high_interest_classifies_known_interest():
    assert classify_recommendation(0.9, 0.1, 0.5) == "known_interest"
