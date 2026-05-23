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
    You will receive raw release notes and merged PRs from the past week. Produce a
    theme-sliced digest for a vLLM-savvy engineer who is deciding what to track,
    test or upgrade.

    Output GitHub-flavored markdown. Use exactly these level-2 sections in this order;
    OMIT any section that has nothing material this window (don't write "nothing this
    week" — just leave the section out):

    ## TL;DR
    Two to four sentences of plain prose. What was the overall shape of the week — perf,
    model coverage, hardware, infra? Anyone who reads only this paragraph should know
    whether the week is worth investigating.

    ## Kernels & attention
    1-4 bullets on FlashAttention/FlashInfer, MLA, Lightning Attention, custom CUDA kernels.

    ## Quantization
    1-4 bullets on FP8 / FP4 / AWQ / GPTQ / GGUF / BnB work, calibration, kernel speedups.

    ## Parallelism & scheduling
    1-4 bullets on TP/PP/EP/SP, chunked prefill, prefix caching, PD disaggregation, KV transfer.

    ## Model support
    1-4 bullets on new architectures, multimodal, audio, embedding/reward, deprecations.

    ## Hardware
    1-4 bullets on AMD/MI300X, TPU, Trainium, CPU, Blackwell-specific work.

    ## API & serving
    1-4 bullets on OpenAI-compatible API, tool calling, structured outputs, observability.

    ## Watch list
    1-3 bullets flagging RFCs / contentious threads / breaking changes worth following.

    Rules:
    - Each bullet ≤ 1 line. No filler.
    - Cite PRs as `#1234` inline. Don't fabricate numbers.
    - Skip CI / lint / docs unless notable.
    - Place each PR under the single most-relevant theme; don't double-list.
""").strip()


# Bump when RELEASE_SYSTEM changes meaningfully — invalidates cached summaries.
RELEASE_PROMPT_VERSION = "v4"


RELEASE_SYSTEM = dedent("""
    You are advising a vLLM operator on whether to upgrade to this release. You will
    receive the raw release-notes markdown. Your job is to answer their decision,
    not to paraphrase the notes.

    A separate "Supported models" card grid and a "Capability matrix" are rendered
    elsewhere on the page. Do NOT list individual added models here. Do NOT restate
    "expanded model coverage" as a bullet — it's covered already.

    Output GitHub-flavored markdown with these level-3 headings in this order. Sections
    are required unless explicitly marked optional.

    ### Verdict
    One line in bold, picked from exactly one of:
      **Upgrade.**  /  **Upgrade with caveats.**  /  **Wait.**  /  **Skip.**
    Followed by one short sentence justifying it. No bullets.

    ### Who should upgrade
    Two to four bullets. Each bullet describes a concrete profile of user/workload
    and whether this release is a win for them (e.g. "DeepSeek-V3 operators on H100 —
    yes, MLA + DeepEP perf wins land here").

    ### Likely to break
    Two to four bullets covering deprecations, default flips, behavior changes, removed
    APIs, or load-bearing perf regressions. If genuinely nothing breaks, write ONE
    bullet: "- Nothing material — drop-in upgrade." Do NOT omit this section.

    ### Performance & infra changes (optional)
    Up to four bullets summarising perf, kernel, quantization, scheduler, or hardware
    work. Each bullet prefixed with an inline-bold label, one of: **Performance:**,
    **Quantization:**, **Kernels:**, **Scheduler:**, **Hardware:**, **API:**.
    Cite PR refs `#1234` inline. Omit this whole section if there's nothing
    non-trivial to report.

    Rules:
    - Don't fabricate PRs, models or features. Stick to what's in the notes.
    - Skip pure docs/CI churn.
    - Do NOT include the release title or any H1/H2 heading (caller adds those).
    - No preamble, no closing remarks — start directly with `### Verdict`.
""").strip()


# DAILY_SYSTEM has been removed. We no longer emit per-day digests — see
# WEEKLY_SYSTEM, which is theme-sliced and the only digest the site renders.


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
    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"
    if os.getenv("GITHUB_TOKEN", "").strip():
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
    # Only a weekly theme-sliced digest is supported. We clamp very-short windows
    # to 7 days so callers passing days=1 still get useful output instead of
    # whatever the upstream prompt does with an empty payload.
    if days < 3:
        days = 7
    system = WEEKLY_SYSTEM

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
