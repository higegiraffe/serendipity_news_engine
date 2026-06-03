from __future__ import annotations

import argparse

from .db import init_db
from .embedding_job import embed_missing_articles
from .feed_loader import fetch_articles
from .profile import init_interest_profile, update_profile_from_feedback
from .recommender import score_articles
from .utils import load_settings


def cmd_init(_args) -> None:
    init_db()
    init_interest_profile()


def cmd_fetch(_args) -> None:
    settings = load_settings()
    fetch_articles(settings.get("app", {}).get("max_articles_per_run", 200))


def cmd_embed(_args) -> None:
    settings = load_settings()
    embed_missing_articles(settings.get("app", {}).get("max_articles_per_run", 200))


def cmd_score(_args) -> None:
    update_profile_from_feedback()
    score_articles()


def cmd_run(args) -> None:
    cmd_fetch(args)
    cmd_embed(args)
    cmd_score(args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Personal serendipity news engine")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, func in {"init": cmd_init, "fetch": cmd_fetch, "embed": cmd_embed, "score": cmd_score, "run": cmd_run}.items():
        p = sub.add_parser(name)
        p.set_defaults(func=func)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
