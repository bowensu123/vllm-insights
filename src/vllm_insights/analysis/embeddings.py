"""Text embeddings via GitHub Models (default) or OpenAI direct.

We default to **GitHub Models** so this works on every cron with just the
default `GITHUB_TOKEN` — no extra secret to configure. GitHub Models exposes
OpenAI's `text-embedding-3-small` (and others) under
`https://models.github.ai/inference/embeddings`, free for public-repo
workflows. If `OPENAI_API_KEY` is set we use OpenAI directly instead, which
is useful for higher rate limits or for running outside CI.

Backend selection priority:

  1. `EMBED_BACKEND` env var, if set to `github` or `openai`
  2. `OPENAI_API_KEY` set       → openai
  3. `GITHUB_TOKEN` set         → github (the default in CI)
  4. nothing set                → skip with a log line

Caching: each PR/issue's embedding input is hashed (sha1 of the normalised
title+body) and stored alongside the vector. On re-runs we skip any entity
whose current hash already has a vector. This means an edited PR body
re-embeds; an unchanged one doesn't.

Dimensions: default 256. Plenty of signal for k-means at this scale and
keeps the SQLite-encoded vector well under 1KB per row. Both backends
forward the `dimensions` parameter to the underlying OpenAI model.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import httpx

from ..db import connect


# Backend definitions. The 'model' is what we pass to the API; for GitHub
# Models it's the `provider/name` form, for OpenAI direct it's just the name.
#
# Per-backend caps:
#   batch        — how many inputs we pack into one POST
#   pace_sec     — minimum wall-clock gap between successive POSTs. GH Models
#                  free tier is ~15 requests/min on embeddings, so 4s is a
#                  safe floor; OpenAI direct allows much more.
#   max_batches  — soft per-run cap so a single sync doesn't blow the daily
#                  quota. GH Models free tier is ~150 requests/day; we leave
#                  headroom for retries / re-embeds. Hourly cron × 30 batches
#                  × 32 inputs = ~23k PRs/day theoretical, capped at ~4800/day
#                  by the daily request quota.
_BACKENDS = {
    "github": {
        "url": "https://models.github.ai/inference/embeddings",
        "model": "openai/text-embedding-3-small",
        "env_token": "GITHUB_TOKEN",
        "batch": 32,
        "pace_sec": 4.0,
        "max_batches": 30,
    },
    "openai": {
        "url": "https://api.openai.com/v1/embeddings",
        "model": "text-embedding-3-small",
        "env_token": "OPENAI_API_KEY",
        "batch": 96,
        "pace_sec": 0.1,
        "max_batches": 200,
    },
}
DEFAULT_DIM = 256
TIMEOUT = 60.0


class RateLimitExhausted(Exception):
    """Server kept telling us to back off. Not a bug — just out of budget for
    this run. Caller catches this and stops cleanly; remaining work resumes
    on the next cron because we already committed prior batches."""
    pass


def _detect_backend(explicit: str | None = None) -> str | None:
    """Pick a backend per the priority order. Returns None if no creds."""
    if explicit:
        if explicit not in _BACKENDS:
            raise ValueError(f"unknown embed backend {explicit!r}")
        if not os.getenv(_BACKENDS[explicit]["env_token"], "").strip():
            return None
        return explicit
    env = os.getenv("EMBED_BACKEND", "").strip().lower()
    if env:
        return _detect_backend(env)
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    if os.getenv("GITHUB_TOKEN", "").strip():
        return "github"
    return None


# Back-compat alias for code reading these as module-level constants.
DEFAULT_MODEL = _BACKENDS["openai"]["model"]


def _content_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:16]


def _prepare_text(title: str | None, body: str | None,
                  *, body_limit: int = 1200) -> str:
    """Compose the text we embed for one PR / issue. We cap the body to keep
    token usage bounded — the first ~1.2K characters of a PR description carry
    most of the signal anyway."""
    title = (title or "").strip()
    body = (body or "").strip()
    if len(body) > body_limit:
        body = body[:body_limit] + "…"
    if not body:
        return title
    return f"{title}\n\n{body}"


def _sleep_from_headers(resp, attempt: int, *, cap: float = 60.0) -> float:
    """Decide how long to sleep after a 429/503. Honors `Retry-After` first
    (in seconds OR an HTTP-date), then falls back to capped exponential.
    Returns the sleep duration so the caller can log it."""
    ra = resp.headers.get("Retry-After") if resp is not None else None
    if ra:
        try:
            sec = float(ra)
            return min(max(sec, 1.0), cap)
        except ValueError:
            # HTTP-date format — bail to exponential rather than parse it
            pass
    # x-ratelimit-reset on GH Models gives a unix timestamp; if present, use it
    if resp is not None:
        reset = resp.headers.get("x-ratelimit-reset")
        if reset:
            try:
                wait = int(reset) - int(time.time())
                if 0 < wait < cap:
                    return float(wait + 1)
            except ValueError:
                pass
    return min(2 ** attempt, cap)


def _post_batch(client: httpx.Client, url: str, key: str, inputs: list[str],
                model: str, dim: int | None) -> list[list[float]]:
    """One POST. Raises RateLimitExhausted if the server keeps backing us off."""
    payload: dict = {"model": model, "input": inputs}
    if dim:
        payload["dimensions"] = dim
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    last_status = None
    for attempt in range(6):
        try:
            r = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as e:
            time.sleep(min(2 ** attempt, 30))
            last_status = f"network:{type(e).__name__}"
            continue
        last_status = r.status_code
        if r.status_code in (429, 503):
            wait = _sleep_from_headers(r, attempt)
            print(f"  rate-limited ({r.status_code}); sleeping {wait:.0f}s "
                  f"(attempt {attempt + 1}/6)")
            time.sleep(wait)
            continue
        if r.status_code >= 500:
            time.sleep(min(2 ** attempt, 30))
            continue
        if r.status_code == 403:
            # Daily quota typically surfaces here ("RateLimitReached" body).
            # No point retrying — caller should stop cleanly.
            body = (r.text or "")[:300]
            raise RateLimitExhausted(
                f"403 on {url} (likely daily quota): {body}"
            )
        r.raise_for_status()
        data = r.json()
        return [d["embedding"] for d in data["data"]]
    raise RateLimitExhausted(
        f"embeddings endpoint backed off 6x (last={last_status}): {url}"
    )


def embed_entities(
    db_path: Path,
    kind: str,
    *,
    backend: str | None = None,
    model: str | None = None,
    dim: int = DEFAULT_DIM,
    limit: int | None = None,
    force: bool = False,
) -> int:
    """Embed every PR (kind='pr') or every issue (kind='issue') we don't yet
    have a vector for. Returns the number of new vectors written."""
    selected = _detect_backend(backend)
    if not selected:
        print(f"No embed backend available "
              f"(set GITHUB_TOKEN or OPENAI_API_KEY); skipping {kind}")
        return 0
    cfg = _BACKENDS[selected]
    url = cfg["url"]
    model = model or cfg["model"]
    key = os.getenv(cfg["env_token"], "").strip()
    batch = cfg["batch"]
    print(f"Embedding {kind} via {selected} backend "
          f"(model={model}, batch={batch})")

    if kind == "pr":
        select_sql = "SELECT number AS id, title, body FROM pull_requests ORDER BY number DESC"
    elif kind == "issue":
        select_sql = "SELECT number AS id, title, '' AS body FROM issues ORDER BY number DESC"
    else:
        raise ValueError(f"unknown kind {kind!r}")
    if limit:
        select_sql += f" LIMIT {int(limit)}"

    with connect(db_path) as conn:
        rows = conn.execute(select_sql).fetchall()

    # Build (id, text) list; skip rows already embedded with same hash + model.
    to_embed: list[tuple[int, str]] = []
    with connect(db_path) as conn:
        for r in rows:
            text = _prepare_text(r["title"], r["body"] if "body" in r.keys() else "")
            if not text.strip():
                continue
            h = _content_hash(text)
            cached = conn.execute(
                "SELECT 1 FROM embeddings WHERE kind = ? AND entity_id = ? AND model = ?"
                "  AND substr(vec, 1, 18) = ?",
                (kind, r["id"], model, f'{{"h":"{h}",'),
            ).fetchone()
            if cached and not force:
                continue
            to_embed.append((r["id"], text))

    if not to_embed:
        return 0

    pace_sec = cfg.get("pace_sec", 0.0)
    max_batches = cfg.get("max_batches", 200)
    total_batches = (len(to_embed) + batch - 1) // batch
    print(f"  {len(to_embed)} entities to embed in {total_batches} batch(es); "
          f"cap={max_batches} per run, pace={pace_sec}s")

    n_written = 0
    n_batches = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    stopped_early = False
    last_post_at = 0.0
    with httpx.Client(timeout=TIMEOUT) as client, connect(db_path) as conn:
        for i in range(0, len(to_embed), batch):
            if n_batches >= max_batches:
                stopped_early = True
                print(f"  hit per-run cap ({max_batches} batches); resuming next run")
                break
            chunk = to_embed[i:i + batch]
            texts = [t for _, t in chunk]
            # Pace requests so we stay under the per-minute limit.
            gap = pace_sec - (time.time() - last_post_at)
            if gap > 0:
                time.sleep(gap)
            try:
                vectors = _post_batch(client, url, key, texts, model, dim)
            except RateLimitExhausted as e:
                # Persist what we already wrote; resume next run.
                print(f"  rate-limit exhausted: {e}")
                stopped_early = True
                break
            last_post_at = time.time()
            n_batches += 1
            for (entity_id, text), vec in zip(chunk, vectors):
                # Prepend the hash inside the JSON blob so cache lookup is one
                # SQL prefix-match (avoids a separate column).
                blob = json.dumps({"h": _content_hash(text), "v": vec})
                conn.execute(
                    """INSERT INTO embeddings(kind, entity_id, model, dim, vec, created_at)
                       VALUES(?, ?, ?, ?, ?, ?)
                       ON CONFLICT(kind, entity_id, model) DO UPDATE SET
                         dim = excluded.dim, vec = excluded.vec,
                         created_at = excluded.created_at""",
                    (kind, entity_id, model, len(vec), blob, now_iso),
                )
                n_written += 1
    suffix = " (partial — more next run)" if stopped_early else ""
    print(f"  wrote {n_written} new vector(s){suffix}")
    return n_written


def load_vectors(db_path: Path, kind: str, *, model: str | None = None
                 ) -> tuple[list[int], list[list[float]]]:
    """Return parallel arrays ``(entity_ids, vectors)`` for everything embedded.

    When *model* is None (the default), selects only the most recently used
    model to avoid silently mixing vectors from different embedding spaces.
    If multiple models are present a warning is printed so operators know to
    re-embed with a single backend.
    """
    ids: list[int] = []
    vecs: list[list[float]] = []
    with connect(db_path) as conn:
        if model:
            selected = model
        else:
            # Pick the model whose most recent embedding was created latest.
            model_row = conn.execute(
                "SELECT model FROM embeddings WHERE kind = ? "
                "GROUP BY model ORDER BY MAX(created_at) DESC LIMIT 1",
                (kind,),
            ).fetchone()
            if not model_row:
                return [], []
            selected = model_row["model"]
            all_models = [
                r["model"] for r in conn.execute(
                    "SELECT DISTINCT model FROM embeddings WHERE kind = ?", (kind,)
                ).fetchall()
            ]
            if len(all_models) > 1:
                print(
                    f"  load_vectors: {len(all_models)} embedding models found "
                    f"for kind={kind!r}; using most recent ({selected!r}). "
                    "Re-run `analyze --embed` with a single backend to consolidate."
                )

        rows = conn.execute(
            "SELECT entity_id, vec FROM embeddings WHERE kind = ? AND model = ?",
            (kind, selected),
        ).fetchall()

    for r in rows:
        obj = json.loads(r["vec"])
        ids.append(r["entity_id"])
        vecs.append(obj["v"])
    return ids, vecs
