"""Generate a daily markdown report from the SQLite cache."""
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from .analyzer.queries import (
    releases_df, prs_df, commits_df, classify_pr_by_title, merge_time_stats,
)


def generate_daily_report(db_path: Path, days: int = 7) -> str:
    now = datetime.now(timezone.utc)
    since = pd.Timestamp(now - timedelta(days=days), tz="UTC")

    rel = releases_df(db_path)
    prs = prs_df(db_path)
    cm = commits_df(db_path)

    lines: list[str] = [f"# vLLM activity report — {now:%Y-%m-%d}", ""]

    # ----- Summary cards -----
    lines += ["## Summary", ""]
    lines += [f"- **Releases (all-time):** {len(rel)}"]
    if not rel.empty:
        lines += [f"- **Latest release:** [`{rel.iloc[-1]['tag']}`]({rel.iloc[-1]['url']}) "
                  f"on {rel.iloc[-1]['published_at']:%Y-%m-%d}"]
        med = rel["interval_days"].dropna().median()
        if pd.notna(med):
            lines += [f"- **Median release interval:** {med:.1f} days"]
    lines += [f"- **PRs (all-time):** {len(prs)}"]
    if not prs.empty:
        merged = prs.dropna(subset=["merged_at"])
        recent_merged = merged[merged["merged_at"] >= since]
        lines += [f"- **PRs merged in last {days}d:** {len(recent_merged)}"]
        med_h = merged["merge_hours"].dropna().median()
        if pd.notna(med_h):
            lines += [f"- **Median merge time (all-time):** {med_h:.1f} h"]
    lines += [f"- **Commits (cached):** {len(cm)}"]
    lines += [""]

    # ----- Recent releases -----
    if not rel.empty:
        recent_rel = rel[rel["published_at"] >= since]
        if not recent_rel.empty:
            lines += [f"## Releases in last {days} days", ""]
            for _, r in recent_rel.iterrows():
                lines += [f"- [`{r['tag']}`]({r['url']}) — {r['published_at']:%Y-%m-%d}"]
            lines += [""]

    # ----- PR tech distribution (last N days) -----
    if not prs.empty:
        window = prs[prs["created_at"] >= since].copy()
        if not window.empty:
            window["tech"] = window["title"].apply(classify_pr_by_title)
            dist = window.groupby("tech").size().sort_values(ascending=False)
            lines += [f"## PR activity by tech area (last {days} days)", "",
                      "| Area | PRs |", "|---|---:|"]
            for area, n in dist.items():
                lines += [f"| {area} | {n} |"]
            lines += [""]

    # ----- Top merged PRs -----
    if not prs.empty:
        merged = prs.dropna(subset=["merged_at"])
        recent = merged[merged["merged_at"] >= since].sort_values("merged_at", ascending=False)
        if not recent.empty:
            lines += [f"## Recently merged PRs (last {days} days, top 30)", ""]
            for _, p in recent.head(30).iterrows():
                rel_tag = f" → `{p['release_tag']}`" if p.get("release_tag") else ""
                lines += [f"- [#{p['number']}]({p['url']}) {p['title']} "
                          f"— @{p['author']}{rel_tag}"]
            lines += [""]

    # ----- Top contributors -----
    if not cm.empty:
        recent_cm = cm[cm["committed_at"] >= since]
        if not recent_cm.empty:
            top = recent_cm.groupby("author").size().sort_values(ascending=False).head(10)
            lines += [f"## Top committers (last {days} days)", "",
                      "| Author | Commits |", "|---|---:|"]
            for a, n in top.items():
                lines += [f"| {a} | {n} |"]
            lines += [""]

    # ----- Monthly merge time trend -----
    if not prs.empty:
        stats = merge_time_stats(prs)
        if not stats.empty:
            lines += ["## Merge time trend (last 12 months)", "",
                      "| Month | Median (h) | PRs merged |", "|---|---:|---:|"]
            for _, row in stats.tail(12).iterrows():
                lines += [f"| {row['month']} | {row['median']:.1f} | {int(row['count'])} |"]
            lines += [""]

    return "\n".join(lines)
