"""Per-release inventory snapshots — backbone for the time-series charts.

For each of the last N stable releases we fetch the upstream git-tree at
that tag, then count:

  - Model architectures (parsing registry.py at the tag)
  - Files under quantization / attention / platforms / distributed /
    spec_decode / lora — same source-scan rules used for current state.

Snapshots are cached forever per (tag, kind, name) — a release never
changes, so once we've ingested it we don't refetch. First run costs N
tree fetches (currently ~12); incremental runs cost zero.

Output table: `historical_inventory(snapshot_tag, published_at, kind, name,
source_path)`. Downstream chart code groups by tag + kind for the curves.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console

from ..db import connect, set_sync_state
from ..github import GitHubClient
from ..registry_sync import parse_registry_source
from ..source_scan import discover_features

console = Console()


def _recent_release_tags(db_path: Path, limit: int = 12) -> list[tuple[str, str]]:
    """Most recent N stable releases as (tag, published_at), newest first."""
    with connect(db_path) as conn:
        rows = conn.execute(
            """SELECT tag, published_at FROM releases
               WHERE is_prerelease = 0
               ORDER BY published_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [(r["tag"], r["published_at"]) for r in rows]


def _have_snapshot(conn, tag: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM historical_inventory WHERE snapshot_tag = ? LIMIT 1", (tag,),
    ).fetchone() is not None


def _fetch_registry_at_tag(client: GitHubClient, tag: str) -> str | None:
    """Pull the raw text of `vllm/model_executor/models/registry.py` at `tag`.
    Returns None if the file isn't at that path on that revision (older
    releases used a different path). We hit raw.githubusercontent.com so this
    doesn't burn authenticated API rate budget — public repo only."""
    import httpx
    url = (f"https://raw.githubusercontent.com/{client.repo}/{tag}/"
           f"vllm/model_executor/models/registry.py")
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as c:
            r = c.get(url)
            if r.status_code != 200:
                return None
            return r.text
    except Exception:  # noqa: BLE001
        return None


def sync_history(client: GitHubClient, db_path: Path, *,
                 max_releases: int = 12, skip_cached: bool = True) -> int:
    """Snapshot inventory for the most recent stable releases. Returns the
    number of new tags ingested."""
    tags = _recent_release_tags(db_path, limit=max_releases)
    if not tags:
        console.print("[yellow]No stable releases in cache — sync --releases first[/]")
        return 0

    n_new = 0
    with connect(db_path) as conn:
        for tag, published_at in tags:
            if skip_cached and _have_snapshot(conn, tag):
                continue
            try:
                tree = client.get_tree(tree_sha=tag, recursive=True)
            except Exception as e:  # noqa: BLE001
                console.print(f"[yellow]tree fetch failed for {tag}:[/] "
                              f"{type(e).__name__}: {e}")
                continue
            if tree.get("truncated"):
                console.print(f"[yellow]tree truncated at {tag}; skipping[/]")
                continue

            # Source-scan: quant / attention / platform / parallel / spec_decode / lora.
            feature_rows = discover_features(tree)
            for kind, name, src_path, _sha in feature_rows:
                conn.execute(
                    """INSERT OR REPLACE INTO historical_inventory
                       (snapshot_tag, published_at, kind, name, source_path)
                       VALUES (?, ?, ?, ?, ?)""",
                    (tag, published_at, kind, name, src_path),
                )

            # Architectures: parse registry.py at the tag.
            reg_src = _fetch_registry_at_tag(client, tag)
            if reg_src:
                try:
                    parsed = parse_registry_source(reg_src)
                except Exception:  # noqa: BLE001
                    parsed = {}
                for category, entries in parsed.items():
                    for arch, module, _impl in entries:
                        conn.execute(
                            """INSERT OR REPLACE INTO historical_inventory
                               (snapshot_tag, published_at, kind, name, source_path)
                               VALUES (?, ?, ?, ?, ?)""",
                            (tag, published_at, "arch",
                             arch,
                             f"vllm/model_executor/models/{module}.py"),
                        )

            n_new += 1

        set_sync_state(conn, "history", datetime.now(timezone.utc).isoformat())

    console.print(f"[cyan]History:[/] {n_new} new release(s) snapshotted")
    return n_new


def counts_over_time(db_path: Path, kind: str) -> list[dict]:
    """Return `[{tag, published_at, count}]` for one kind, oldest tag first.

    Used to draw the "how many arches did vLLM ship at each release" curve.
    """
    with connect(db_path) as conn:
        rows = conn.execute(
            """SELECT snapshot_tag, published_at, COUNT(*) AS n
               FROM historical_inventory
               WHERE kind = ?
               GROUP BY snapshot_tag, published_at
               ORDER BY published_at ASC""",
            (kind,),
        ).fetchall()
    return [dict(r) for r in rows]


def items_at(db_path: Path, kind: str, tag: str) -> set[str]:
    """Items of one kind at one snapshot. Used for "added in release X" diffs."""
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT name FROM historical_inventory WHERE kind = ? AND snapshot_tag = ?",
            (kind, tag),
        ).fetchall()
    return {r["name"] for r in rows}
