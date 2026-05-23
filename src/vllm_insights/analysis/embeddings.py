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
_BACKENDS = {
    "github": {
        "url": "https://models.github.ai/inference/embeddings",
        "model": "openai/text-embedding-3-small",
        "env_token": "GITHUB_TOKEN",
        # GitHub Models has stricter rate limits than OpenAI direct; smaller
        # batch size + slightly longer back-off keeps us under the per-minute cap.
        "batch": 32,
    },
    "openai": {
        "url": "https://api.openai.com/v1/embeddings",
        "model": "text-embedding-3-small",
        "env_token": "OPENAI_API_KEY",
        "batch": 96,
    },
}
DEFAULT_DIM = 256
TIMEOUT = 60.0


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


def _post_batch(client: httpx.Client, url: str, key: str, inputs: list[str],
                model: str, dim: int | None) -> list[list[float]]:
    payload: dict = {"model": model, "input": inputs}
    if dim:
        payload["dimensions"] = dim
    for attempt in range(6):
        r = client.post(url, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }, json=payload)
        if r.status_code == 429:
            time.sleep(min(2 ** attempt, 30))
            continue
        if r.status_code >= 500:
            time.sleep(min(2 ** attempt, 30))
            continue
        r.raise_for_status()
        data = r.json()
        return [d["embedding"] for d in data["data"]]
    raise RuntimeError(f"embeddings endpoint rate-limited 6x: {url}")


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
        select_sql = "SELECT number AS id, title, body FROM pull_requests"
    elif kind == "issue":
        select_sql = "SELECT number AS id, title, '' AS body FROM issues"
    else:
        raise ValueError(f"unknown kind {kind!r}")
    if limit:
        select_sql += f" ORDER BY id DESC LIMIT {int(limit)}"

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

    n_written = 0
    now_iso = datetime.now(timezone.utc).isoformat()
    with httpx.Client(timeout=TIMEOUT) as client, connect(db_path) as conn:
        for i in range(0, len(to_embed), batch):
            chunk = to_embed[i:i + batch]
            texts = [t for _, t in chunk]
            vectors = _post_batch(client, url, key, texts, model, dim)
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
    return n_written


def load_vectors(db_path: Path, kind: str, *, model: str | None = None
                 ) -> tuple[list[int], list[list[float]]]:
    """Return parallel arrays `(entity_ids, vectors)` for everything embedded.

    If `model` is None, returns vectors for every model we have on file —
    useful when callers don't know which backend created them. In practice
    the GH-Models and OpenAI direct models produce vectors in the same space
    (they're both `text-embedding-3-small`), so mixing is fine.
    """
    ids: list[int] = []
    vecs: list[list[float]] = []
    with connect(db_path) as conn:
        if model:
            rows = conn.execute(
                "SELECT entity_id, vec FROM embeddings WHERE kind = ? AND model = ?",
                (kind, model),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT entity_id, vec FROM embeddings WHERE kind = ?",
                (kind,),
            ).fetchall()
    for r in rows:
        obj = json.loads(r["vec"])
        ids.append(r["entity_id"])
        vecs.append(obj["v"])
    return ids, vecs
