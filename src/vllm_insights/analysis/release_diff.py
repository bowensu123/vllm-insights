"""Aggregate file changes between adjacent releases by top-level directory.

For each pair (R_{n-1}, R_n) of stable releases we call /compare on GitHub,
which returns the files changed between the two tags (with per-file
additions/deletions). We bucket those files by directory prefix — the most
meaningful prefix is usually two segments deep (e.g. `vllm/model_executor`,
`vllm/attention`, `vllm/v1`) so we use that.

The output ends up looking like:

  v0.9.0 → v0.10.0     vllm/model_executor   files=42  +5102/-3001
                       vllm/v1                files=28  +3214/-1408
                       benchmarks             files=4   +210/-12

…which is the answer to "where did the code actually move last release?".
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

from rich.console import Console

from ..db import connect
from ..github import GitHubClient

console = Console()

# How many path segments to keep when bucketing. Two is the sweet spot for
# vLLM: `vllm/model_executor`, `vllm/attention`, `vllm/v1`, `tests/v1`, …
_BUCKET_DEPTH = 2


def _bucket(path: str) -> str:
    parts = path.split("/")
    if len(parts) <= _BUCKET_DEPTH:
        return path
    return "/".join(parts[:_BUCKET_DEPTH])


def _list_release_pairs(db_path: Path, limit: int = 12) -> list[tuple[str, str]]:
    """Most recent N stable releases as (older, newer) adjacent pairs."""
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT tag FROM releases WHERE is_prerelease = 0 "
            "ORDER BY published_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    tags = [r["tag"] for r in rows]
    # tags is newest-first; pair adjacent ones with older→newer order.
    return [(tags[i + 1], tags[i]) for i in range(len(tags) - 1)]


def sync_release_diffs(
    client: GitHubClient,
    db_path: Path,
    *,
    max_pairs: int = 8,
    skip_cached: bool = True,
    rate_pause: float = 0.5,
) -> int:
    """For each recent release pair, call /compare and aggregate by directory.

    `max_pairs` bounds the number of /compare calls (each can be ~200KB of
    JSON for a busy release). `skip_cached` reuses prior aggregations — a
    release pair never changes, so once we've ingested it we don't refetch.
    """
    pairs = _list_release_pairs(db_path, limit=max_pairs + 2)[:max_pairs]
    if not pairs:
        return 0

    n_pairs = 0
    with connect(db_path) as conn:
        for from_tag, to_tag in pairs:
            if skip_cached:
                cached = conn.execute(
                    "SELECT 1 FROM release_diffs WHERE from_tag = ? AND to_tag = ? LIMIT 1",
                    (from_tag, to_tag),
                ).fetchone()
                if cached:
                    continue

            try:
                cmp = client.compare(from_tag, to_tag)
            except Exception as e:  # noqa: BLE001
                console.print(f"[yellow]compare failed {from_tag}..{to_tag}:[/] "
                              f"{type(e).__name__}: {e}")
                continue

            buckets: dict[str, dict[str, int]] = {}
            for f in cmp.get("files") or []:
                path = f.get("filename") or ""
                if not path:
                    continue
                key = _bucket(path)
                b = buckets.setdefault(key, {"files": 0, "add": 0, "del": 0})
                b["files"] += 1
                b["add"] += f.get("additions") or 0
                b["del"] += f.get("deletions") or 0

            for dir_, agg in buckets.items():
                conn.execute(
                    """INSERT INTO release_diffs(from_tag, to_tag, dir,
                                                 files, additions, deletions)
                       VALUES(?, ?, ?, ?, ?, ?)
                       ON CONFLICT(from_tag, to_tag, dir) DO UPDATE SET
                         files=excluded.files,
                         additions=excluded.additions,
                         deletions=excluded.deletions""",
                    (from_tag, to_tag, dir_, agg["files"], agg["add"], agg["del"]),
                )
            n_pairs += 1
            time.sleep(rate_pause)  # be polite to the API

    console.print(f"[cyan]Release diffs:[/] {n_pairs} new pair(s) ingested")
    return n_pairs


def load_drift_for_pair(db_path: Path, from_tag: str, to_tag: str,
                        top: int = 12) -> list[dict]:
    """Top `top` directories by additions+deletions for a single pair."""
    with connect(db_path) as conn:
        rows = conn.execute(
            """SELECT dir, files, additions, deletions
               FROM release_diffs
               WHERE from_tag = ? AND to_tag = ?
               ORDER BY (additions + deletions) DESC LIMIT ?""",
            (from_tag, to_tag, top),
        ).fetchall()
    return [dict(r) for r in rows]


def latest_pair(db_path: Path) -> tuple[str, str] | None:
    """The most recent release pair that we have drift data for."""
    with connect(db_path) as conn:
        row = conn.execute(
            """SELECT from_tag, to_tag FROM release_diffs
               GROUP BY from_tag, to_tag
               ORDER BY to_tag DESC LIMIT 1"""
        ).fetchone()
    if not row:
        return None
    return row["from_tag"], row["to_tag"]
