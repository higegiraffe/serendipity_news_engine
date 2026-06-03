from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*_args, **_kwargs):
        return False


def has_openai_key() -> bool:
    load_dotenv()
    return bool(os.getenv("OPENAI_API_KEY"))


def summarize_article(title: str, summary: str | None) -> str:
    if not has_openai_key():
        return (summary or title)[:240]
    try:
        from openai import OpenAI
        client = OpenAI()
        response = client.responses.create(model="gpt-4.1-mini", input=f"この記事を日本語で1文に要約してください。\nタイトル: {title}\n概要: {summary or ''}")
        return response.output_text.strip()
    except Exception:
        return (summary or title)[:240]


def summarize_interest_axis(feedback_text: str) -> str:
    if not has_openai_key():
        return "フィードバックは記事ベクトルを通じて反映されます。言語レベルのメモ生成には OpenAI API キーを設定してください。"
    try:
        from openai import OpenAI
        client = OpenAI()
        response = client.responses.create(model="gpt-4.1-mini", input=f"このフィードバックから、関心軸を日本語で最大5個抽出してください。\n{feedback_text}")
        return response.output_text.strip()
    except Exception as exc:
        return f"LLMメモを生成できませんでした: {exc}"
