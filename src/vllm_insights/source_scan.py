"""Enumerate vLLM features by scanning the upstream repo's git tree.

The previous version of this project shipped a hand-curated capability matrix.
That's the opposite of what this tool should do — every cell was unverifiable
opinion, and would rot the moment upstream refactored. This module replaces
that with a one-shot git-tree scan that turns each "feature kind" into a list
of concrete files in the vLLM source.

We use the GitHub Trees API (one call, ~7k entries today for vLLM) so we
don't burn the rate budget walking directories.

What we enumerate today, and where it lives in the tree:

  quantization  → vllm/model_executor/layers/quantization/*.py
  platform      → vllm/platforms/*.py
  attention     → vllm/attention/**.py (post-V1 layout flat in v1/attention/)
  parallel      → vllm/distributed/*.py
  spec_decode   → vllm/spec_decode/*.py  OR  vllm/v1/spec_decode/*.py
  lora          → vllm/lora/*.py

Each row has:
  kind, name, source_path, source_sha, last_seen_at

`name` is derived from the filename (stem) — that's what the rest of the
codebase uses to key into PR activity etc.  We deliberately do NOT attach
maturity labels here; that's downstream UI's job, and the only way to source
those honestly is from CI / labels / blog posts (not from this file).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .db import connect, set_sync_state


# Files we exclude from the "name = stem" rule because they're scaffolding,
# not a discrete feature.
_BORING_STEMS = {"__init__", "interface", "base_config", "base", "utils",
                 "common", "registry", "abstract"}


@dataclass(frozen=True)
class _Rule:
    """One enumeration rule.

    `kind`      coarse category shown to the user.
    `prefix`    path prefix in the upstream tree; entries must start with this.
    `also_ok`   optional fallback prefix tried if `prefix` returns 0 hits
                (the tree gets reorganised every few releases; this is the cheap
                way to survive moves like spec_decode → v1/spec_decode).
    """
    kind: str
    prefix: str
    also_ok: tuple[str, ...] = ()


_RULES: tuple[_Rule, ...] = (
    _Rule("quantization", "vllm/model_executor/layers/quantization/"),
    _Rule("platform",     "vllm/platforms/"),
    _Rule("attention",    "vllm/v1/attention/backends/",
                          also_ok=("vllm/attention/backends/", "vllm/attention/")),
    _Rule("parallel",     "vllm/distributed/"),
    _Rule("spec_decode",  "vllm/v1/spec_decode/",
                          also_ok=("vllm/spec_decode/",)),
    _Rule("lora",         "vllm/lora/"),
)


def _name_from_path(path: str) -> str | None:
    """Derive a stable feature name from a path. Returns None for boring
    scaffolding files we don't want to surface."""
    stem = Path(path).stem
    if stem in _BORING_STEMS:
        return None
    return stem


def _matching_files(tree_entries: list[dict], prefix: str) -> list[dict]:
    """Direct .py children of `prefix` (no nested subdirs). We deliberately stay
    one level deep so the matrix doesn't fan out into every utility file."""
    hits = []
    for ent in tree_entries:
        if ent.get("type") != "blob":
            continue
        path = ent.get("path", "")
        if not path.startswith(prefix) or not path.endswith(".py"):
            continue
        tail = path[len(prefix):]
        if "/" in tail:
            continue
        hits.append(ent)
    return hits


def discover_features(tree: dict) -> list[tuple[str, str, str, str | None]]:
    """Apply every rule to a tree response. Returns rows as
    `(kind, name, source_path, sha)`. Tree-api `sha` for the blob is per-file;
    we keep it so the UI can deep-link to a stable revision."""
    entries: list[dict] = tree.get("tree", [])
    rows: list[tuple[str, str, str, str | None]] = []

    for rule in _RULES:
        primary = _matching_files(entries, rule.prefix)
        used_prefix = rule.prefix
        if not primary:
            for alt in rule.also_ok:
                hits = _matching_files(entries, alt)
                if hits:
                    primary, used_prefix = hits, alt
                    break
        for ent in primary:
            name = _name_from_path(ent["path"])
            if name is None:
                continue
            rows.append((rule.kind, name, ent["path"], ent.get("sha")))
        # `used_prefix` retained for debugging; not stored.
        del used_prefix
    return rows


def sync_source_inventory(client, db_path: Path, *, branch: str = "main") -> dict[str, int]:
    """Fetch the upstream tree on `branch`, enumerate features, upsert rows.

    Returns `{kind: count_seen}`. Old rows that didn't reappear this run are
    deleted (unlike `model_registry` which tombstones — here a deleted file
    means the feature was renamed or moved, and we want the next sync to
    surface it again under the new path).
    """
    tree = client.get_tree(tree_sha=branch, recursive=True)
    if tree.get("truncated"):
        # Bail loudly rather than silently dropping rows.
        raise RuntimeError(
            "GitHub git-trees API truncated the response (>100k entries). "
            "Switch to a recursive directory walk."
        )
    rows = discover_features(tree)
    now_iso = datetime.now(timezone.utc).isoformat()
    counts: dict[str, int] = {}

    with connect(db_path) as conn:
        # Drop the old snapshot. A feature is either in upstream or it isn't;
        # tombstoning here would just confuse the UI.
        conn.execute("DELETE FROM source_inventory")
        for kind, name, path, sha in rows:
            counts[kind] = counts.get(kind, 0) + 1
            conn.execute(
                """INSERT INTO source_inventory(kind, name, source_path, source_sha, last_seen_at)
                   VALUES(?, ?, ?, ?, ?)
                   ON CONFLICT(kind, name, source_path) DO UPDATE SET
                       source_sha = excluded.source_sha,
                       last_seen_at = excluded.last_seen_at""",
                (kind, name, path, sha, now_iso),
            )
        set_sync_state(conn, "source_inventory", now_iso)
    return counts


def load_inventory(db_path: Path, kind: str | None = None) -> list[dict]:
    """Return inventory rows, optionally filtered to one kind."""
    sql = "SELECT * FROM source_inventory"
    args: tuple = ()
    if kind:
        sql += " WHERE kind = ?"
        args = (kind,)
    sql += " ORDER BY kind, name"
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def kinds_in_order() -> list[tuple[str, str]]:
    """Display order + human label for each `kind` we surface."""
    return [
        ("quantization", "Quantization"),
        ("attention",    "Attention backends"),
        ("parallel",     "Parallelism & distributed"),
        ("spec_decode",  "Speculative decoding"),
        ("lora",         "LoRA & adapters"),
        ("platform",     "Hardware platforms"),
    ]


def pr_activity_for_inventory(
    db_path: Path,
    days: int = 90,
) -> dict[str, int]:
    """Count PRs (last `days`) that touched each inventoried source_path.

    Returns `{source_path: pr_count}`. Reads from pr_files. If pr_files is
    empty (no PRs synced yet, or no `--with-files` flag) the dict is empty
    and the UI should just hide the activity column rather than show zeros.
    """
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT prf.path AS path, COUNT(DISTINCT prf.pr_number) AS n
            FROM pr_files prf
            JOIN pull_requests p ON p.number = prf.pr_number
            JOIN source_inventory s ON s.source_path = prf.path
            WHERE p.merged_at IS NOT NULL
              AND p.merged_at >= datetime('now', ?)
            GROUP BY prf.path
            """,
            (f"-{int(days)} days",),
        ).fetchall()
    return {r["path"]: r["n"] for r in rows}
