"""LLM-powered weekly changelog summary."""
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from textwrap import dedent

import pandas as pd

from .db import connect


SYSTEM_PROMPT = dedent("""
    You are a release-notes editor for the vLLM project (a high-throughput LLM inference engine).
    You will receive raw release notes and merged PRs from the past week. Produce a tight markdown
    summary aimed at a vLLM-savvy engineer who wants to know what changed and why it matters.

    Output sections (omit any that have no content):
      ## Highlights — 3-6 bullets of the most impactful items, plain English, with PR/release refs
      ## New model support
      ## Performance & kernels
      ## Hardware (AMD/TPU/CPU/...)
      ## API & serving
      ## Notable bug fixes
      ## Breaking changes

    Rules:
    - Cite items with PR refs `#1234` or tag refs `v0.x.y` inline. Don't fabricate numbers.
    - Be terse: each bullet ≤ 1 line. No filler ("This week we...", "Various improvements...").
    - Skip pure docs/CI churn unless notable.
""").strip()


def collect_week(db_path: Path, days: int = 7) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    since_iso = since.isoformat()

    with connect(db_path) as conn:
        releases = conn.execute(
            "SELECT tag, name, published_at, body FROM releases "
            "WHERE published_at >= ? ORDER BY published_at",
            (since_iso,),
        ).fetchall()
        prs = conn.execute(
            "SELECT number, title, author, merged_at, release_tag, labels, url "
            "FROM pull_requests WHERE merged_at >= ? ORDER BY merged_at DESC",
            (since_iso,),
        ).fetchall()

    return {
        "since": since_iso,
        "releases": [dict(r) for r in releases],
        "prs": [dict(p) for p in prs],
    }


def render_input(payload: dict, max_prs: int = 200) -> str:
    parts = [f"Window: since {payload['since']}", ""]
    if payload["releases"]:
        parts.append("## Releases this week")
        for r in payload["releases"]:
            parts.append(f"### {r['tag']} ({r['published_at']})")
            body = (r.get("body") or "").strip()
            # cap each release body to keep prompt bounded
            if len(body) > 8000:
                body = body[:8000] + "\n…(truncated)"
            parts.append(body or "_(no body)_")
            parts.append("")
    parts.append(f"## Merged PRs this week (showing up to {max_prs})")
    for p in payload["prs"][:max_prs]:
        rel = f" → {p['release_tag']}" if p.get("release_tag") else ""
        labels = f" [{p['labels']}]" if p.get("labels") else ""
        parts.append(f"- #{p['number']} {p['title']} (@{p['author']}){labels}{rel}")
    if len(payload["prs"]) > max_prs:
        parts.append(f"_…and {len(payload['prs']) - max_prs} more_")
    return "\n".join(parts)


def summarize_week(db_path: Path, days: int = 7, model: str | None = None) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key.startswith("sk-ant-xxx"):
        raise RuntimeError("ANTHROPIC_API_KEY not set in .env")
    model = model or os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    payload = collect_week(db_path, days=days)
    user_input = render_input(payload)

    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_input}],
    )
    text = "".join(block.text for block in resp.content if block.type == "text")

    header = (
        f"# vLLM weekly summary — {datetime.now(timezone.utc):%Y-%m-%d}\n\n"
        f"_Window: last {days} days · "
        f"{len(payload['releases'])} release(s), {len(payload['prs'])} merged PR(s) · "
        f"model: `{model}`_\n\n"
    )
    return header + text.strip() + "\n"
