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
        response = client.responses.create(model="gpt-4.1-mini", input=f"Summarize this article in Japanese in one sentence.\nTitle: {title}\nSummary: {summary or ''}")
        return response.output_text.strip()
    except Exception:
        return (summary or title)[:240]


def summarize_interest_axis(feedback_text: str) -> str:
    if not has_openai_key():
        return "Feedback is reflected through article vectors; add an OpenAI key for language-level memo generation."
    try:
        from openai import OpenAI
        client = OpenAI()
        response = client.responses.create(model="gpt-4.1-mini", input=f"Extract up to five Japanese interest axes from this feedback.\n{feedback_text}")
        return response.output_text.strip()
    except Exception as exc:
        return f"LLM memo unavailable: {exc}"
