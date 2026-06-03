from __future__ import annotations

import hashlib
from email.utils import parsedate_to_datetime

from .db import connect, save_article
from .utils import CONFIG_DIR, load_yaml


def _entry_date(entry) -> str | None:
    raw = entry.get("published") or entry.get("updated")
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw).isoformat()
    except Exception:
        return raw


def load_feeds() -> list[dict]:
    config = load_yaml(CONFIG_DIR / "feeds.yaml")
    return [feed for feed in config.get("feeds", []) if feed.get("enabled", True)]


def fetch_articles(max_articles: int | None = None) -> int:
    try:
        import feedparser
    except ModuleNotFoundError:
        print("[fetch] feedparser がインストールされていません。実行してください: pip install -r requirements.txt")
        return 0
    new_count = 0
    conn = connect()
    for feed in load_feeds():
        try:
            parsed = feedparser.parse(feed["url"])
        except Exception as exc:
            print(f"[fetch] 取得失敗: {feed.get('name')} {exc}")
            continue
        for entry in parsed.entries[: max_articles or None]:
            title = (entry.get("title") or "").strip()
            url = (entry.get("link") or "").strip()
            if not title or not url:
                continue
            summary = (entry.get("summary") or entry.get("description") or "").strip()
            digest = hashlib.sha256(f"{title}\n{summary}\n{url}".encode("utf-8")).hexdigest()
            article = {"source_name": feed.get("name"), "source_category": feed.get("category"), "title": title, "summary": summary, "url": url, "published_at": _entry_date(entry), "content_hash": digest, "source_score": float(feed.get("trust_weight", 0.5))}
            if save_article(conn, article):
                new_count += 1
    conn.close()
    print(f"[fetch] 新規記事: {new_count}")
    return new_count
