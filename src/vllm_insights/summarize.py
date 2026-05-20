"""LLM-powered changelog summary (daily / weekly).

Backends:
  - github   : GitHub Models inference API (uses GITHUB_TOKEN with models:read)
  - anthropic: Anthropic SDK (uses ANTHROPIC_API_KEY)

Pick via LLM_BACKEND env var or --backend flag. Defaults to "github" if GITHUB_TOKEN
is present, else "anthropic".
"""
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from textwrap import dedent

import httpx

from .db import connect


# Match #1234 only when NOT already inside a markdown link, e.g. avoid touching
# the "1234" inside "[#1234](url)".  We require the preceding char to not be "[".
_PR_RE = re.compile(r"(?<![\[\w])#(\d{2,6})\b")
# Match vX.Y[.Z][.suffix] not already inside a link.
_TAG_RE = re.compile(r"(?<![\[/\w])(v\d+\.\d+(?:\.\d+)?(?:\.[a-zA-Z0-9]+)?)\b")


def link_refs(text: str, repo: str) -> str:
    """Hyperlink #1234 -> PR URL and vX.Y.Z -> release URL in markdown text."""
    base = f"https://github.com/{repo}"
    text = _PR_RE.sub(rf"[#\1]({base}/pull/\1)", text)
    text = _TAG_RE.sub(rf"[\1]({base}/releases/tag/\1)", text)
    return text


WEEKLY_SYSTEM = dedent("""
    You are a release-notes editor for vLLM (a high-throughput LLM inference engine).
    You will receive raw release notes and merged PRs from the past week. Produce a tight
    markdown summary for a vLLM-savvy engineer who wants to know what changed and why it matters.

    Output sections (omit any that have no content):
      ## Highlights — 3-6 bullets of the most impactful items
      ## New model support
      ## Performance & kernels
      ## Hardware (AMD/TPU/CPU/...)
      ## API & serving
      ## Notable bug fixes
      ## Breaking changes

    Rules:
    - Cite items with PR refs `#1234` or tag refs `v0.x.y` inline. Don't fabricate numbers.
    - Be terse: each bullet ≤ 1 line. No filler.
    - Skip pure docs/CI churn unless notable.
""").strip()


# Bump when RELEASE_SYSTEM changes meaningfully — invalidates cached summaries.
RELEASE_PROMPT_VERSION = "v2"


RELEASE_SYSTEM = dedent("""
    You are summarizing one vLLM release for engineers who want a quick overview
    before reading the full notes. You will receive the raw release-notes markdown.

    A separate, structured "Supported models" section is rendered elsewhere on the page,
    so DO NOT list individual added models here. You may mention "expanded model coverage"
    in the overview at a high level, but no per-model bullets.

    Produce:
      **Overview** (2-3 sentences): what this release is about, who should care,
      any headline change. May briefly note "new model support" generally without listing models.

      **Key changes**: 4-7 bullets covering NON-model topics only, grouped under inline-bold
      labels: **Performance:**, **Hardware:**, **Quantization:**, **API & serving:**,
      **Engine/scheduler:**. Each bullet ≤ 1 line, cite PR refs `#1234` inline.

      **Upgrade notes** (1-3 bullets, omit if empty): deprecations, breaking changes,
      behavior shifts users must watch out for.

    Rules:
    - Don't fabricate PRs or features. Stick to what's in the notes.
    - Skip pure docs/CI churn unless headline-worthy.
    - Do NOT include "Model support" or "New models" bullets — those are handled separately.
    - Output GitHub-flavored markdown. Do NOT include the release title (caller adds it).
""").strip()


DAILY_SYSTEM = dedent("""
    You are summarizing one day of activity in the vLLM repo for engineers tracking the project.
    You will receive the day's merged PRs and any release that landed.

    Produce a concise markdown digest:
      ## What landed today
      - 5-10 bullets, grouped loosely by theme (model support / kernels / perf / bug fixes / API)
      - Each bullet: terse, with PR ref `#1234` inline
    ## Notable
      - 1-3 items worth a second look (breaking changes, big perf wins, new hardware, new model families)
      - Omit this section if nothing qualifies.

    Rules:
    - Don't fabricate PR numbers or tags.
    - Skip pure CI / lint / docs unless they're load-bearing.
    - If the day had no merges, output: "_No merges today._"
""").strip()


def collect_window(db_path: Path, days: int) -> dict:
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
    return {"since": since_iso, "days": days,
            "releases": [dict(r) for r in releases],
            "prs": [dict(p) for p in prs]}


def render_input(payload: dict, max_prs: int = 200) -> str:
    parts = [f"Window: last {payload['days']} day(s), since {payload['since']}", ""]
    if payload["releases"]:
        parts.append("## Releases in window")
        for r in payload["releases"]:
            parts.append(f"### {r['tag']} ({r['published_at']})")
            body = (r.get("body") or "").strip()
            if len(body) > 8000:
                body = body[:8000] + "\n…(truncated)"
            parts.append(body or "_(no body)_")
            parts.append("")
    parts.append(f"## Merged PRs in window (up to {max_prs})")
    for p in payload["prs"][:max_prs]:
        rel = f" → {p['release_tag']}" if p.get("release_tag") else ""
        labels = f" [{p['labels']}]" if p.get("labels") else ""
        parts.append(f"- #{p['number']} {p['title']} (@{p['author']}){labels}{rel}")
    if len(payload["prs"]) > max_prs:
        parts.append(f"_…and {len(payload['prs']) - max_prs} more_")
    return "\n".join(parts)


def _detect_backend(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.getenv("LLM_BACKEND", "").strip().lower()
    if env:
        return env
    if os.getenv("GITHUB_TOKEN"):
        return "github"
    return "anthropic"


def _call_github_models(system: str, user: str, model: str) -> str:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set for github backend")
    url = "https://models.github.ai/inference/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 2000,
        "temperature": 0.3,
    }
    with httpx.Client(timeout=60.0) as c:
        r = c.post(url, headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }, json=payload)
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"]


def _call_anthropic(system: str, user: str, model: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not api_key or api_key.startswith("sk-ant-xxx"):
        raise RuntimeError("ANTHROPIC_API_KEY not set for anthropic backend")
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model, max_tokens=2000, system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


DEFAULT_MODELS = {
    "github": "openai/gpt-4o-mini",
    "anthropic": "claude-haiku-4-5",
}


def summarize_window(
    db_path: Path,
    days: int = 7,
    model: str | None = None,
    backend: str | None = None,
    repo: str = "vllm-project/vllm",
    include_header: bool = True,
) -> str:
    backend = _detect_backend(backend)
    model = model or os.getenv("LLM_MODEL") or DEFAULT_MODELS[backend]
    system = DAILY_SYSTEM if days <= 1 else WEEKLY_SYSTEM

    payload = collect_window(db_path, days=days)
    user_input = render_input(payload)

    if backend == "github":
        text = _call_github_models(system, user_input, model)
    elif backend == "anthropic":
        text = _call_anthropic(system, user_input, model)
    else:
        raise ValueError(f"Unknown backend: {backend}")

    text = link_refs(text.strip(), repo)

    if not include_header:
        return text + "\n"

    label = "daily" if days <= 1 else f"{days}-day"
    header = (
        f"# vLLM {label} digest — {datetime.now(timezone.utc):%Y-%m-%d}\n\n"
        f"_Window: last {days} day(s) · "
        f"{len(payload['releases'])} release(s), {len(payload['prs'])} merged PR(s) · "
        f"backend: `{backend}` · model: `{model}`_\n\n"
    )
    return header + text + "\n"


# Backward-compat alias used by existing CLI/workflow imports.
summarize_week = summarize_window


def summarize_release(
    db_path: Path,
    tag: str | None = None,
    model: str | None = None,
    backend: str | None = None,
    repo: str = "vllm-project/vllm",
    force: bool = False,
) -> tuple[str, str]:
    """LLM-summarize a single release's body. Caches in release_summaries.

    Returns (tag, summary_markdown). If tag is None, picks the latest stable release.
    If a cached summary exists and force=False, returns it without calling the LLM.
    """
    with connect(db_path) as conn:
        if tag is None:
            row = conn.execute(
                "SELECT tag, body, name FROM releases WHERE is_prerelease = 0 "
                "ORDER BY published_at DESC LIMIT 1"
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT tag, body, name FROM releases WHERE tag = ?", (tag,)
            ).fetchone()
        if not row:
            raise RuntimeError(f"No release found for tag={tag!r}")
        tag = row["tag"]
        body = row["body"] or ""

        if not force:
            cached = conn.execute(
                "SELECT summary, model FROM release_summaries WHERE tag = ?", (tag,)
            ).fetchone()
            # Cache is invalidated if model field doesn't carry the current prompt version tag.
            if cached and cached["model"] and RELEASE_PROMPT_VERSION in (cached["model"] or ""):
                return tag, cached["summary"]

    backend = _detect_backend(backend)
    model = model or os.getenv("LLM_MODEL") or DEFAULT_MODELS[backend]

    # Cap body to keep prompt bounded (some vLLM releases have 20k+ char notes)
    if len(body) > 20000:
        body = body[:20000] + "\n…(truncated)"

    user_input = f"Release: {tag}\n\nRaw release notes:\n\n{body}"

    if backend == "github":
        text = _call_github_models(RELEASE_SYSTEM, user_input, model)
    elif backend == "anthropic":
        text = _call_anthropic(RELEASE_SYSTEM, user_input, model)
    else:
        raise ValueError(f"Unknown backend: {backend}")

    summary = link_refs(text.strip(), repo)

    now_iso = datetime.now(timezone.utc).isoformat()
    # Stamp the prompt version into the model field so cache invalidates on prompt changes.
    model_stamped = f"{model} [{RELEASE_PROMPT_VERSION}]"
    with connect(db_path) as conn:
        conn.execute(
            """INSERT INTO release_summaries(tag, summary, model, backend, generated_at)
               VALUES(?,?,?,?,?)
               ON CONFLICT(tag) DO UPDATE SET
                 summary=excluded.summary, model=excluded.model,
                 backend=excluded.backend, generated_at=excluded.generated_at""",
            (tag, summary, model_stamped, backend, now_iso),
        )
    return tag, summary
