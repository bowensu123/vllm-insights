# vllm-insights

GitHub insights for [vllm-project/vllm](https://github.com/vllm-project/vllm).
Focus: release dynamics, commit activity, PR flow, technical-area trends.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
copy .env.example .env
# edit .env, set GITHUB_TOKEN (public_repo scope is enough)
```

## Usage

```powershell
# Incremental sync (first run takes a while)
vllm-insights sync --releases --prs --commits

# Launch dashboard
vllm-insights dash
# or: streamlit run src/vllm_insights/app.py
```

## Layout

```
src/vllm_insights/
  db.py              # SQLite schema + helpers
  github.py          # GraphQL/REST client with rate-limit handling
  fetcher/           # Incremental sync per entity
  analyzer/          # pandas aggregations
  release_notes.py   # Parse markdown release notes into sections
  app.py             # Streamlit dashboard
  cli.py             # Typer CLI
```
