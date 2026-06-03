# Personal Serendipity News Engine

A local-first article recommendation engine that collects RSS entries, embeds titles and summaries, scores them against a personal interest profile, and learns from your feedback.

The goal is not to collect every article. The goal is to estimate interests that are hard to express as search terms, then surface known-interest, adjacent-interest, and surprise articles with a visible reason.

## Setup on Windows

```powershell
cd C:\Users\10003963\Documents\User\python\serendipity_news_engine
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

OpenAI is optional. Without `OPENAI_API_KEY`, the app uses local embeddings. If `sentence-transformers` is not installed yet, it falls back to deterministic hash embeddings so the CLI and tests still run.

## Commands

```powershell
python -m src.main init
python -m src.main fetch
python -m src.main embed
python -m src.main score
python -m src.main run
streamlit run src/ui_streamlit.py
```

## Configuration

- Add or disable RSS feeds in `config/feeds.yaml`.
- Edit seed interests in `config/interests.yaml`.
- Change embedding provider and scoring weights in `config/settings.yaml`.
- Set `embedding.provider` to `openai` and add `OPENAI_API_KEY` to `.env` for OpenAI embeddings.

## Scoring

```text
final_score = similarity_weight * interest_score + novelty_weight * novelty_score + freshness_weight * freshness_score + source_weight * source_score
```

Recommendation types are `known_interest`, `adjacent_interest`, and `surprise`. Feedback is saved in SQLite and used to update profile vectors and source scores.

The database is stored at `data/app.db`. Article body scraping and web search APIs are intentionally left for later phases; the MVP displays generated search keywords for future exploration.

## Tests

```powershell
python -m pytest
```

## Future Extensions

Web search providers, article body extraction, RSS source suggestions, daily reports, and interest profile visualization.
