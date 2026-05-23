"""Homepage hero — upgrade verdict (when available) or daily takeaway.

Two modes
---------
verdict mode  (default when a release with an LLM summary exists and
               the release is < 45 days old):

  v0.9.2  ·  3 days ago
  Should you upgrade?

  ┌── Upgrade. Major FlashInfer speedups, no breaking changes. ──────────┐

  [⚡ 8 perf claims]  [🧬 3 new models]  [✓ No regressions]  [Full notes →]

  → DeepSeek-V3 operators on H100 — yes, MLA + DeepEP wins land here.
  → FP8 users on A100 — GEMM kernel improvements, worth upgrading.
  → Llama-3 / AWQ users — no breaking changes, drop-in.

  ── status strip ──────────────────────────────────────────────────────
  [subscribe form]

default mode  (no verdict / stale release):

  <eyebrow>Today in vLLM · 2026-05-23</eyebrow>
  <h1>A live view of what vLLM is shipping.</h1>
  <p>Release clause. Hottest topic. Most-reacted PR. Open regressions.</p>
  ── status strip ──
  [subscribe form]
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from .analysis.social import hottest_recent_prs
from .analysis.topics import cluster_momentum
from .db import connect
from .ui import status_strip, subscribe_form


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _latest_release(db_path: Path) -> dict | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT r.tag, r.published_at, rs.summary "
            "FROM releases r LEFT JOIN release_summaries rs ON rs.tag = r.tag "
            "WHERE r.is_prerelease = 0 ORDER BY r.published_at DESC LIMIT 1"
        ).fetchone()
    return dict(row) if row else None


def _open_watch_count(db_path: Path) -> int:
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
    """Extract the bold one-liner verdict that follows ``### Verdict``."""
    if not summary_md:
        return None
    in_verdict = False
    for ln in summary_md.splitlines():
        s = ln.strip()
        if s.startswith("### Verdict"):
            in_verdict = True
            continue
        if in_verdict:
            if not s:
                continue
            if s.startswith("#"):
                break
            return s.replace("**", "").replace("__", "").strip()
    return None


def _extract_who_bullets(summary_md: str, *, max_bullets: int = 3) -> list[str]:
    """Return the first *max_bullets* bullets from ``### Who should upgrade``."""
    bullets: list[str] = []
    in_section = False
    for ln in summary_md.splitlines():
        s = ln.strip()
        if "### who should upgrade" in s.lower():
            in_section = True
            continue
        if in_section:
            if s.startswith("###"):
                break
            if s.startswith(("-", "*")):
                bullet = s.lstrip("-* ").strip().replace("**", "").replace("__", "")
                if bullet:
                    bullets.append(bullet)
                    if len(bullets) >= max_bullets:
                        break
    return bullets


def _release_signals(db_path: Path, tag: str, published_at: str) -> dict:
    """Compute concrete signal counts for a release's chip row."""
    with connect(db_path) as conn:
        prev = conn.execute(
            "SELECT published_at FROM releases WHERE is_prerelease = 0 "
            "AND published_at < ? ORDER BY published_at DESC LIMIT 1",
            (published_at,),
        ).fetchone()
        since = prev["published_at"] if prev else published_at[:10]

        perf_n = conn.execute(
            "SELECT COUNT(DISTINCT pc.pr_number) AS n FROM perf_claims pc "
            "JOIN pull_requests p ON p.number = pc.pr_number "
            "WHERE p.merged_at >= ? AND p.merged_at <= ?",
            (since, published_at),
        ).fetchone()["n"] or 0

        model_n = conn.execute(
            "SELECT COUNT(*) AS n FROM release_sections "
            "WHERE tag = ?",
            (tag,),
        ).fetchone()["n"] or 0

        watch_n = conn.execute(
            "SELECT COUNT(*) AS n FROM issues WHERE state = 'OPEN' AND ("
            "labels LIKE '%regression%' OR labels LIKE '%release-blocker%')"
        ).fetchone()["n"] or 0

    return {"perf_n": int(perf_n), "model_n": int(model_n), "watch_n": int(watch_n)}


# ---------------------------------------------------------------------------
# Verdict hero (rich mode)
# ---------------------------------------------------------------------------

def _render_verdict_hero(
    rel: dict,
    verdict: str,
    signals: dict,
    who_bullets: list[str],
    db_path: Path,
    newsletter_username: str,
) -> str:
    tag = escape(rel["tag"])
    published = (rel.get("published_at") or "")[:10]

    try:
        d = datetime.fromisoformat(
            rel["published_at"].replace("Z", "+00:00")
        )
        age_days = (datetime.now(timezone.utc) - d).days
        age_str = (
            "today" if age_days == 0 else
            "yesterday" if age_days == 1 else
            f"{age_days} days ago"
        )
    except Exception:  # noqa: BLE001
        age_str = published

    # Signal chips
    chips: list[str] = []
    if signals["perf_n"]:
        chips.append(
            f'<span class="chip chip-perf">⚡ {signals["perf_n"]} perf claims</span>'
        )
    if signals["model_n"]:
        chips.append(
            f'<span class="chip chip-model">🧬 {signals["model_n"]} release items</span>'
        )
    if signals["watch_n"] == 0:
        chips.append('<span class="chip chip-ok">✓ No open regressions</span>')
    else:
        chips.append(
            f'<span class="chip chip-watch">⚠️ {signals["watch_n"]} open regression'
            f'{"s" if signals["watch_n"] != 1 else ""}</span>'
        )
    chips.append('<a class="chip chip-link" href="#latest-release">Full release notes ↓</a>')
    chips_html = "\n  ".join(chips)

    # "Who should upgrade" bullets
    who_html = ""
    if who_bullets:
        lis = "\n    ".join(
            f"<li>{escape(b)}</li>" for b in who_bullets
        )
        who_html = f'<div class="verdict-who"><ul>\n    {lis}\n  </ul></div>'

    strip = build_status_strip(db_path)
    sub = subscribe_form(newsletter_username)

    return f"""
<section class="hero hero-verdict" aria-labelledby="hero-verdict-title">
  <div class="verdict-eyebrow">
    <span class="ver-tag">{tag}</span>
    <span class="ver-sep">·</span>
    <span class="ver-age">{escape(age_str)}</span>
  </div>
  <p class="verdict-q">Should you upgrade?</p>
  <h1 class="verdict-headline" id="hero-verdict-title">{escape(verdict)}</h1>
  <div class="signal-chips">
  {chips_html}
  </div>
  {who_html}
  {strip}
  {sub}
</section>
""".strip()


# ---------------------------------------------------------------------------
# Default hero (fallback / no verdict)
# ---------------------------------------------------------------------------

def build_hero_takeaway(db_path: Path) -> tuple[str, str]:
    """Return `(eyebrow, body_html)`. Unchanged from prior implementation."""
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
    with connect(db_path) as conn:
        total_row = conn.execute(
            "SELECT COUNT(*) AS n FROM pull_requests"
        ).fetchone()
        emb_row = conn.execute(
            "SELECT COUNT(DISTINCT entity_id) AS n FROM embeddings WHERE kind = 'pr'"
        ).fetchone()
    return int(emb_row["n"] or 0), int(total_row["n"] or 0)


def build_status_strip(db_path: Path) -> str:
    with connect(db_path) as conn:
        max_ts = conn.execute(
            "SELECT MAX(last_synced_at) AS t FROM sync_state"
        ).fetchone()
        last_sync = (max_ts and max_ts["t"]) or ""
        n_releases = conn.execute("SELECT COUNT(*) AS n FROM releases").fetchone()["n"]
        n_prs = conn.execute("SELECT COUNT(*) AS n FROM pull_requests").fetchone()["n"]
        n_issues = conn.execute("SELECT COUNT(*) AS n FROM issues").fetchone()["n"]
        n_arches = conn.execute(
            "SELECT COUNT(*) AS n FROM model_registry WHERE removed_at IS NULL"
        ).fetchone()["n"]
        # 7-day PR delta for context
        pr_7d = conn.execute(
            "SELECT COUNT(*) AS n FROM pull_requests "
            "WHERE merged_at IS NOT NULL AND merged_at >= datetime('now', '-7 days')"
        ).fetchone()["n"] or 0

    pr_label = f"{n_prs:,}"
    pr_hint = f"+{pr_7d} this week" if pr_7d else None

    rows = [
        ("Updated", last_sync[:16].replace("T", " ") if last_sync else "—", "UTC"),
        ("Releases", f"{n_releases:,}", None),
        ("PRs", pr_label, pr_hint),
        ("Issues", f"{n_issues:,}", None),
        ("Architectures", f"{n_arches:,}", None),
    ]
    return status_strip(rows)


# ---------------------------------------------------------------------------
# Public entry point used by build_site.py
# ---------------------------------------------------------------------------

def build_upgrade_hero(
    db_path: Path,
    repo_url: str,
    newsletter_username: str = "",
) -> str:
    """Return the hero section HTML.

    Uses verdict mode when:
      - A release with an LLM summary exists
      - The verdict one-liner can be extracted
      - The release is < 45 days old

    Otherwise falls back to the standard signal-paragraph hero.
    """
    rel = _latest_release(db_path)

    if rel:
        verdict = _verdict_first_line(rel.get("summary"))
        if verdict and rel.get("published_at"):
            try:
                d = datetime.fromisoformat(
                    rel["published_at"].replace("Z", "+00:00")
                )
                age_days = (datetime.now(timezone.utc) - d).days
            except Exception:  # noqa: BLE001
                age_days = 999

            if age_days < 45:
                signals = _release_signals(db_path, rel["tag"], rel["published_at"])
                who_bullets = _extract_who_bullets(rel.get("summary") or "")
                return _render_verdict_hero(
                    rel, verdict, signals, who_bullets,
                    db_path, newsletter_username,
                )

    # Fallback: standard takeaway hero
    eyebrow, body_html = build_hero_takeaway(db_path)
    strip = build_status_strip(db_path)
    sub = subscribe_form(newsletter_username)
    return f"""
<section class="hero" aria-labelledby="hero-title">
  <p class="hero-eyebrow">{eyebrow}</p>
  <h1 class="hero-title" id="hero-title">A live view of what vLLM is shipping.</h1>
  <div class="hero-body">{body_html}</div>
  {strip}
  {sub}
</section>
""".strip()
