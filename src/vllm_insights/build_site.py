"""Build a static HTML dashboard under docs/ for GitHub Pages.

Generates:
  docs/index.html           — interactive Plotly dashboard
  docs/reports/index.md     — list of daily reports
  docs/weekly/index.md      — list of weekly summaries

Daily / weekly markdown files are expected to already live under docs/reports/ and
docs/weekly/ (produced by the report / summarize commands when --out points there).
"""
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio

from .analyzer.queries import (
    releases_df, prs_df, commits_df, classify_pr_by_title, merge_time_stats,
)


PAGE_CSS = """
:root { color-scheme: light dark; }
body { font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
       max-width: 1200px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
header { border-bottom: 1px solid #ddd3; padding-bottom: 1rem; margin-bottom: 1.5rem; }
h1 { margin: 0 0 .3rem; font-size: 1.6rem; }
h2 { margin-top: 2rem; font-size: 1.25rem; border-bottom: 1px solid #ddd3; padding-bottom: .3rem; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
         gap: .75rem; margin: 1rem 0; }
.card { padding: .75rem 1rem; border: 1px solid #ddd5; border-radius: 8px; }
.card .v { font-size: 1.5rem; font-weight: 600; }
.card .l { font-size: .8rem; opacity: .7; }
nav a { margin-right: 1rem; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #ddd3;
         opacity: .65; font-size: .85rem; }
.chart { margin: 1rem 0; }
"""


def _fig_html(fig, div_id: str) -> str:
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", div_id=div_id,
                       config={"displaylogo": False})


def _card(value: str, label: str) -> str:
    return f'<div class="card"><div class="v">{escape(value)}</div><div class="l">{escape(label)}</div></div>'


def build_index(db_path: Path, docs_dir: Path, repo: str) -> Path:
    docs_dir.mkdir(parents=True, exist_ok=True)
    rel = releases_df(db_path)
    prs = prs_df(db_path)
    cm = commits_df(db_path)
    now = datetime.now(timezone.utc)

    # ---- summary cards ----
    cards = []
    cards.append(_card(str(len(rel)), "Releases"))
    if not rel.empty:
        med = rel["interval_days"].dropna().median()
        cards.append(_card(f"{med:.1f}d" if pd.notna(med) else "—", "Median release interval"))
        cards.append(_card(rel.iloc[-1]["tag"], "Latest release"))
    cards.append(_card(str(len(prs)), "PRs cached"))
    if not prs.empty:
        merged = prs.dropna(subset=["merged_at"])
        med_h = merged["merge_hours"].dropna().median()
        cards.append(_card(f"{med_h:.1f}h" if pd.notna(med_h) else "—", "Median merge time"))
    cards.append(_card(str(len(cm)), "Commits cached"))
    cards_html = '<div class="cards">' + "".join(cards) + "</div>"

    # ---- charts ----
    charts: list[str] = []

    if not rel.empty:
        d = rel.dropna(subset=["interval_days"])
        if not d.empty:
            fig = px.scatter(d, x="published_at", y="interval_days", hover_data=["tag"],
                             title="Release cadence (days between releases)")
            charts.append(_fig_html(fig, "chart-release"))

    if not prs.empty:
        stats = merge_time_stats(prs)
        if not stats.empty:
            fig = px.line(stats, x="month", y="median", markers=True,
                          title="Median PR merge time per month (hours)")
            charts.append(_fig_html(fig, "chart-merge"))

        v = prs.copy()
        v["month"] = v["created_at"].dt.to_period("M").astype(str)
        vol = v.groupby(["month", "state"]).size().reset_index(name="count")
        fig = px.bar(vol, x="month", y="count", color="state", title="PRs created per month")
        charts.append(_fig_html(fig, "chart-volume"))

        recent = prs[prs["created_at"] >= pd.Timestamp(now, tz="UTC") - pd.Timedelta(days=180)].copy()
        if not recent.empty:
            recent["tech"] = recent["title"].apply(classify_pr_by_title)
            dist = (recent.groupby("tech").size().reset_index(name="count")
                    .sort_values("count", ascending=False))
            fig = px.bar(dist, x="tech", y="count",
                         title="PR distribution by tech area (last 180 days)")
            charts.append(_fig_html(fig, "chart-tech"))

    if not cm.empty:
        c = cm.copy()
        c["week"] = c["committed_at"].dt.to_period("W").astype(str)
        weekly = c.groupby("week").size().reset_index(name="commits")
        fig = px.line(weekly, x="week", y="commits", title="Commits per week")
        charts.append(_fig_html(fig, "chart-commits"))

        top = (c.groupby("author").size().reset_index(name="commits")
               .sort_values("commits", ascending=False).head(20))
        fig = px.bar(top, x="author", y="commits", title="Top 20 committers (cached window)")
        charts.append(_fig_html(fig, "chart-authors"))

    charts_html = '\n'.join(f'<div class="chart">{c}</div>' for c in charts) \
        or '<p><em>No data yet — run <code>vllm-insights sync --all</code> first.</em></p>'

    repo_url = f"https://github.com/{repo}"
    body = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>vLLM Insights</title>
<style>{PAGE_CSS}</style>
</head><body>
<header>
  <h1>vLLM GitHub Insights</h1>
  <div>Tracking <a href="{repo_url}">{escape(repo)}</a> · updated {now:%Y-%m-%d %H:%M UTC}</div>
  <nav style="margin-top:.6rem">
    <a href="reports/">Daily reports</a>
    <a href="weekly/">Weekly LLM summaries</a>
    <a href="{repo_url}">Source repo</a>
  </nav>
</header>
{cards_html}
<h2>Trends</h2>
{charts_html}
<footer>Generated by vllm-insights. Data from the GitHub REST API,
cached locally to SQLite, refreshed daily via GitHub Actions.</footer>
</body></html>"""
    out = docs_dir / "index.html"
    out.write_text(body, encoding="utf-8")
    return out


def build_report_index(reports_dir: Path, title: str) -> Path | None:
    """Walk reports_dir/*.md and write an index.md sorted newest first."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    files = sorted((p for p in reports_dir.glob("*.md")
                    if p.name not in ("index.md", "latest.md")),
                   reverse=True)
    if not files and not (reports_dir / "latest.md").exists():
        return None
    lines = [f"# {title}", ""]
    if (reports_dir / "latest.md").exists():
        lines += ["- [Latest](latest.md)", ""]
    for f in files:
        lines.append(f"- [{f.stem}]({f.name})")
    out = reports_dir / "index.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
