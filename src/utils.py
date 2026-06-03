from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ModuleNotFoundError:
    yaml = None

ROOT_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "app.db"


def _fallback_config(path: Path) -> dict:
    if path.name == "settings.yaml":
        return {
            "app": {"max_articles_per_run": 200, "recommendation_count": 30, "language": "ja"},
            "embedding": {"provider": "local", "local_model": "paraphrase-multilingual-MiniLM-L12-v2", "openai_model": "text-embedding-3-small"},
            "scoring": {"freshness_weight": 0.15, "source_weight": 0.10, "novelty_weight": 0.15, "similarity_weight": 0.60},
            "ui": {"default_view": "recommended"},
        }
    if path.name == "feeds.yaml":
        return {"feeds": [
            {"name": "NHK News", "url": "https://www.nhk.or.jp/rss/news/cat0.xml", "category": "general_news", "trust_weight": 0.8, "enabled": True},
            {"name": "ITmedia", "url": "https://rss.itmedia.co.jp/rss/2.0/news_bursts.xml", "category": "technology", "trust_weight": 0.8, "enabled": True},
            {"name": "OpenAI Blog", "url": "https://openai.com/news/rss.xml", "category": "ai", "trust_weight": 0.9, "enabled": True},
        ]}
    if path.name == "interests.yaml":
        return {"seed_interests": [
            {"name": "AIによる生活支援", "description": "AIや自動化で生活上の困りごとを解決する技術。", "weight": 1.0},
            {"name": "有用な技術が普及しない理由", "description": "コスト、UX、制度、プライバシー、運用など普及を妨げる要因。", "weight": 1.2},
            {"name": "FX・MT4・売買ロジック", "description": "MT4、インジケーター、EA、フィボナッチ、ピボット、売買戦略。", "weight": 1.0},
            {"name": "機械構造の理由", "description": "機械、車、ロボット、カメラなどの構造がその形になった理由。", "weight": 1.0},
            {"name": "UIと制度の使いにくさ", "description": "作業手順、公共サービス、業務システム、インターフェースの摩擦。", "weight": 1.1},
        ]}
    return {}


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return _fallback_config(path)
    if yaml is None:
        return _fallback_config(path)
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def load_settings() -> dict:
    return load_yaml(CONFIG_DIR / "settings.yaml")


def utc_now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def article_text(title: str | None, summary: str | None) -> str:
    return "\n".join(part for part in [title or "", summary or ""] if part).strip()
