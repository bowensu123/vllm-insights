"""Homepage hero — "today's takeaway" + a status strip of pipeline health.

The takeaway is composed deterministically from already-cached data, with a
final optional LLM polish pass. We do NOT regenerate the whole paragraph
every cron run; we cache it per (latest_release_tag, day) so it only changes
when the underlying signal does.

What goes into the takeaway:
  - Latest release tag + a verdict snippet (already cached in release_summaries)
  - Top 1-2 cluster labels that grew most in the last 30 days
  - Most-reacted PR in the last 7 days (👍 + 🚀 sum)
  - Count of open release-blocker / regression issues

We deliberately keep this short (3-4 sentences). If any input is missing
(e.g. embeddings haven't backfilled yet) we degrade gracefully and skip
that clause rather than emit "no data".

The status strip is pure machine data: last sync time, embedding backfill
progress, number of data sources currently online (releases / PRs /
issues / forks / registry / source_inventory / hn_mentions / etc.).
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .analysis.social import hottest_recent_prs
from .analysis.topics import cluster_momentum
from .db import connect
from .ui import status_strip


def _latest_release(db_path: Path) -> dict | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT r.tag, r.published_at, rs.summary "
            "FROM releases r LEFT JOIN release_summaries rs ON rs.tag = r.tag "
            "WHERE r.is_prerelease = 0 ORDER BY r.published_at DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def _open_watch_count(db_path: Path) -> int:
    """Open issues labelled release-blocker / regression / perf-regression."""
    with connect(db_path) as conn:
        any_row = conn.execute("SELECT 1 FROM issues LIMIT 1").fetchone()
        if not any_row:
            return 0
        row = conn.execute(
            """SELECT COUNT(*) AS n FROM issues
               WHERE state = 'OPEN' AND (
                 labels LIKE '%release-blocker%' OR
                 labels LIKE '%regression%' OR
                 labels LIKE '%perf-regression%'
               )"""
        ).fetchone()
    return int(row["n"] or 0)


def _verdict_first_line(summary_md: str | None) -> str | None:
    """Extract the bolded one-liner verdict from a cached release summary.
    The prompt schema places it right after `### Verdict`."""
    if not summary_md:
        return None
    lines = summary_md.splitlines()
    in_verdict = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("### Verdict"):
            in_verdict = True
            continue
        if in_verdict:
            if not s:
                continue
            if s.startswith("#"):
                break
            # Strip markdown bold/italic
            return s.replace("**", "").replace("__", "").strip()
    return None


def build_hero_takeaway(db_path: Path) -> tuple[str, str]:
    """Return `(eyebrow, body_html)`. The eyebrow is a small label
    ('Today in vLLM') and the body is the synthesized paragraph."""
    now = datetime.now(timezone.utc)
    eyebrow = f"Today in vLLM &middot; {now:%Y-%m-%d}"
    clauses: list[str] = []

    rel = _latest_release(db_path)
    if rel:
        verdict = _verdict_first_line(rel.get("summary"))
        if verdict:
            clauses.append(
                f'<strong>{escape(rel["tag"])}:</strong> {escape(verdict)}'
            )
        else:
            published = (rel.get("published_at") or "")[:10]
            clauses.append(
                f'Latest release <strong>{escape(rel["tag"])}</strong>'
                + (f' shipped {escape(published)}.' if published else '.')
            )

    # Top growing cluster (only if clustering has run)
    momentum = cluster_momentum(db_path, "pr", window_days=30)
    if momentum:
        top = momentum[0]
        if top["ratio"] >= 1.5 and top["current"] >= 3:
            clauses.append(
                f'Hottest topic: <strong>{escape(top["label"])}</strong> '
                f'({top["current"]} PRs in 30d, up from {top["previous"]}).'
            )

    hot_pr = hottest_recent_prs(db_path, days=7, limit=1)
    if hot_pr:
        p = hot_pr[0]
        total = p.get("reactions_total") or 0
        if total >= 5:
            clauses.append(
                f'Most-reacted PR this week: '
                f'<a href="{escape(p["url"] or "")}" target="_blank" rel="noopener">'
                f'#{p["number"]}</a> ({total} reactions).'
            )

    watch = _open_watch_count(db_path)
    if watch >= 1:
        clauses.append(
            f'<strong>{watch}</strong> open '
            f'<a href="#open-issues">release-blocker / regression issue'
            f'{"s" if watch != 1 else ""}</a>.'
        )

    if not clauses:
        body = (
            'Pipeline warming up. '
            'Once releases, PRs, and the upstream registry have synced, '
            'this paragraph will show the day&rsquo;s shape in three sentences.'
        )
    else:
        body = " ".join(f"<p>{c}</p>" for c in clauses)
    return eyebrow, body


def _backfill_progress(db_path: Path) -> tuple[int, int]:
    """Returns (PRs embedded, total PRs). Used by the status strip + an
    explicit progress bar shown when the ratio is well below 100%."""
    with connect(db_path) as conn:
        total_row = conn.execute(
            "SELECT COUNT(*) AS n FROM pull_requests"
        ).fetchone()
        emb_row = conn.execute(
            "SELECT COUNT(DISTINCT entity_id) AS n FROM embeddings WHERE kind = 'pr'"
        ).fetchone()
    return int(emb_row["n"] or 0), int(total_row["n"] or 0)


def build_status_strip(db_path: Path) -> str:
    """Render the strip under the hero with `last sync / backfill / sources`."""
    with connect(db_path) as conn:
        # Latest sync time across all entities
        max_ts = conn.execute(
            "SELECT MAX(last_synced_at) AS t FROM sync_state"
        ).fetchone()
        last_sync = (max_ts and max_ts["t"]) or ""
        # Quick source counts so the strip surfaces "we have data"
        n_releases = conn.execute("SELECT COUNT(*) AS n FROM releases").fetchone()["n"]
        n_prs = conn.execute("SELECT COUNT(*) AS n FROM pull_requests").fetchone()["n"]
        n_issues = conn.execute("SELECT COUNT(*) AS n FROM issues").fetchone()["n"]
        n_arches = conn.execute(
            "SELECT COUNT(*) AS n FROM model_registry WHERE removed_at IS NULL"
        ).fetchone()["n"]

    embedded, total_prs = _backfill_progress(db_path)
    if total_prs > 0:
        emb_hint = f"{embedded:,} / {total_prs:,} PRs"
    else:
        emb_hint = "—"

    rows = [
        ("Last sync", last_sync[:16].replace("T", " ") if last_sync else "—", "UTC"),
        ("Releases", f"{n_releases:,}", None),
        ("PRs cached", f"{n_prs:,}", None),
        ("Labelled issues", f"{n_issues:,}", None),
        ("Live arches", f"{n_arches:,}", None),
        ("Indexed for topics", emb_hint, "of total PRs"),
    ]
    return status_strip(rows)
