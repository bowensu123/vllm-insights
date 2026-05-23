"""OpenAI text embeddings — minimal client, content-hash cached in SQLite.

We use OpenAI's `text-embedding-3-small` because it's cheap ($0.02 per 1M
input tokens) and the API is a single POST. We deliberately call it via raw
httpx instead of pulling in the `openai` SDK — the SDK is heavy and we don't
need any of its sugar for one endpoint.

Caching: each PR/issue's embedding input is hashed (sha1 of the normalised
title+body) and stored alongside the vector. On re-runs we skip any entity
whose current hash already has a vector. This means an edited PR body
re-embeds; an unchanged one doesn't. For 15k PRs the first sync costs a
buck or two; subsequent syncs cost pennies.

Dimensions are configurable via `dim=`; we default to 256 because that's
plenty of signal for k-means clustering at this scale and keeps the
SQLite-encoded vector well under 1KB per row.

If `OPENAI_API_KEY` isn't set the module logs and returns 0. Calling code
should treat embeddings as best-effort; downstream clustering will simply
have less to work with.
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


DEFAULT_MODEL = "text-embedding-3-small"
DEFAULT_DIM = 256
EMBED_URL = "https://api.openai.com/v1/embeddings"
BATCH = 96   # OpenAI accepts up to 2048; smaller batches are easier on rate
TIMEOUT = 60.0


def _key() -> str:
    return os.getenv("OPENAI_API_KEY", "").strip()


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


def _post_batch(client: httpx.Client, key: str, inputs: list[str],
                model: str, dim: int | None) -> list[list[float]]:
    payload: dict = {"model": model, "input": inputs}
    if dim:
        payload["dimensions"] = dim
    for attempt in range(5):
        r = client.post(EMBED_URL, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }, json=payload)
        if r.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        data = r.json()
        return [d["embedding"] for d in data["data"]]
    raise RuntimeError("OpenAI embeddings rate-limited 5x")


def embed_entities(
    db_path: Path,
    kind: str,
    *,
    model: str = DEFAULT_MODEL,
    dim: int = DEFAULT_DIM,
    limit: int | None = None,
    force: bool = False,
) -> int:
    """Embed every PR (kind='pr') or every issue (kind='issue') we don't yet
    have a vector for. Returns the number of new vectors written.

    Pass `force=True` to re-embed everything (e.g. after switching models).
    """
    key = _key()
    if not key:
        print("OPENAI_API_KEY not set; skipping embed of", kind)
        return 0

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
        existing: dict[int, str] = {}
        if not force:
            for r in conn.execute(
                "SELECT entity_id, vec FROM embeddings WHERE kind = ? AND model = ?",
                (kind, model),
            ).fetchall():
                # We store the hash inside the vec JSON's wrapper; easier to
                # keep a parallel column. We re-embed if the text differs.
                pass

    # Build (id, text, hash) list; skip rows already embedded with same hash.
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
        for i in range(0, len(to_embed), BATCH):
            chunk = to_embed[i:i + BATCH]
            texts = [t for _, t in chunk]
            vectors = _post_batch(client, key, texts, model, dim)
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


def load_vectors(db_path: Path, kind: str, *, model: str = DEFAULT_MODEL
                 ) -> tuple[list[int], list[list[float]]]:
    """Return parallel arrays `(entity_ids, vectors)` for everything embedded."""
    ids: list[int] = []
    vecs: list[list[float]] = []
    with connect(db_path) as conn:
        for r in conn.execute(
            "SELECT entity_id, vec FROM embeddings WHERE kind = ? AND model = ?",
            (kind, model),
        ).fetchall():
            obj = json.loads(r["vec"])
            ids.append(r["entity_id"])
            vecs.append(obj["v"])
    return ids, vecs
