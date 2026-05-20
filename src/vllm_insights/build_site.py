"""Build a static HTML dashboard under docs/ for GitHub Pages.

Generates:
  docs/index.html           — interactive Plotly dashboard
  docs/reports/index.md     — list of daily reports
  docs/weekly/index.md      — list of weekly summaries

Daily / weekly markdown files are expected to already live under docs/reports/ and
docs/weekly/ (produced by the report / summarize commands when --out points there).
"""
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio

from .analyzer.queries import (
    releases_df, prs_df, commits_df, classify_pr_by_title, merge_time_stats,
)
from .db import connect
from .models import classify as classify_model, hf_org_url, hf_search_url, looks_like_model_section
from .summarize import link_refs


PAGE_CSS = """
:root { color-scheme: light dark; }
body { font-family: -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
       max-width: 1200px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }
header { border-bottom: 1px solid #ddd3; padding-bottom: 1rem; margin-bottom: 1.5rem; }
h1 { margin: 0 0 .3rem; font-size: 1.6rem; }
h2 { margin-top: 2rem; font-size: 1.25rem; border-bottom: 1px solid #ddd3; padding-bottom: .3rem; }
h3 { margin-top: 1.2rem; margin-bottom: .4rem; font-size: 1.05rem; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
         gap: .75rem; margin: 1rem 0; }
.card { padding: .75rem 1rem; border: 1px solid #ddd5; border-radius: 8px; }
.card .v { font-size: 1.5rem; font-weight: 600; }
.card .l { font-size: .8rem; opacity: .7; }
nav a { margin-right: 1rem; }
footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #ddd3;
         opacity: .65; font-size: .85rem; }
.chart { margin: 1rem 0; }

.release-summary {
  border-left: 3px solid #6cf;
  background: rgba(102,204,255,.08);
  padding: .25rem 1.2rem 1rem;
  margin: 1rem 0 1.5rem;
  border-radius: 0 6px 6px 0;
}
.release-summary h3 { margin-top: 1rem; font-size: 1rem;
                      text-transform: uppercase; letter-spacing: .04em;
                      opacity: .85; border-bottom: 1px dashed #6664;
                      padding-bottom: .25rem; }
.release-summary h3:first-child { margin-top: .8rem; }
.release-summary p { margin: .4rem 0; }
.release-summary ul { padding-left: 1.4rem; margin: .4rem 0; }
.release-summary li { margin: .25rem 0; }
.release-summary .meta { display: block; margin-top: 1rem;
                         font-size: .75rem; opacity: .55; }
"""


def _fig_html(fig, div_id: str) -> str:
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", div_id=div_id,
                       config={"displaylogo": False})


def _card(value: str, label: str) -> str:
    return f'<div class="card"><div class="v">{escape(value)}</div><div class="l">{escape(label)}</div></div>'


def _render_latest_release(db_path: Path, repo: str) -> str:
    """Section showing the latest stable release + LLM summary + supported models."""
    import markdown as md
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT tag, name, published_at, url FROM releases "
            "WHERE is_prerelease = 0 ORDER BY published_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return ""
        latest = dict(row)
        sections = conn.execute(
            "SELECT section, item FROM release_sections WHERE tag = ?",
            (latest["tag"],),
        ).fetchall()
        summary_row = conn.execute(
            "SELECT summary, model, backend FROM release_summaries WHERE tag = ?",
            (latest["tag"],),
        ).fetchone()

    tag = latest["tag"]
    rel_url = latest["url"] or f"https://github.com/{repo}/releases/tag/{tag}"
    name = latest.get("name") or tag

    # Group items from model-related sections by detected vendor
    by_vendor: dict[str, list[tuple[str, str | None]]] = {}
    unknown_items: list[str] = []
    for s in sections:
        if not looks_like_model_section(s["section"]):
            continue
        item = s["item"]
        cls = classify_model(item)
        if cls:
            vendor, org = cls
            by_vendor.setdefault(vendor, []).append((item, org))
        else:
            unknown_items.append(item)

    # Build vendor list HTML
    vendor_html = ""
    if by_vendor or unknown_items:
        chunks = []
        for vendor in sorted(by_vendor.keys()):
            items = by_vendor[vendor]
            org = items[0][1]
            vendor_link = f'<a href="{hf_org_url(org)}" target="_blank" rel="noopener">{escape(vendor)}</a>' if org else escape(vendor)
            li = []
            for item, _org in items:
                # Hyperlink PR refs inside the item text (uses repo, not HF)
                item_html = link_refs(item, repo)
                # Convert markdown [text](url) to <a> for inline rendering
                item_html = re.sub(
                    r"\[([^\]]+)\]\(([^)]+)\)",
                    r'<a href="\2" target="_blank" rel="noopener">\1</a>',
                    item_html,
                )
                # Add an HF search link for the model name itself
                hf_link = f' <a href="{hf_search_url(item)}" target="_blank" rel="noopener" title="Find on Hugging Face">[HF]</a>'
                li.append(f"<li>{item_html}{hf_link}</li>")
            chunks.append(
                f"<details open><summary><strong>{vendor_link}</strong> "
                f"<span style='opacity:.6'>({len(items)})</span></summary>"
                f"<ul>{''.join(li)}</ul></details>"
            )
        if unknown_items:
            li = []
            for item in unknown_items:
                item_html = link_refs(item, repo)
                item_html = re.sub(
                    r"\[([^\]]+)\]\(([^)]+)\)",
                    r'<a href="\2" target="_blank" rel="noopener">\1</a>',
                    item_html,
                )
                hf_link = f' <a href="{hf_search_url(item)}" target="_blank" rel="noopener">[HF]</a>'
                li.append(f"<li>{item_html}{hf_link}</li>")
            chunks.append(
                f"<details><summary><strong>Other / unclassified</strong> "
                f"<span style='opacity:.6'>({len(unknown_items)})</span></summary>"
                f"<ul>{''.join(li)}</ul></details>"
            )
        vendor_html = "\n".join(chunks)
    else:
        vendor_html = "<p><em>No model-support section found in this release's notes.</em></p>"

    published = latest["published_at"][:10] if latest.get("published_at") else "?"

    summary_html = ""
    if summary_row:
        rendered = md.markdown(summary_row["summary"], extensions=["tables", "fenced_code"])
        meta = (
            f"<span class='meta'>LLM summary · "
            f"{escape(summary_row['backend'] or '?')} / "
            f"{escape(summary_row['model'] or '?')}</span>"
        )
        summary_html = f"<div class='release-summary'>{rendered}{meta}</div>"

    return f"""
<h2>Latest release</h2>
<p>
  <a href="{escape(rel_url)}" target="_blank" rel="noopener"><strong>{escape(tag)}</strong></a>
  {escape("— " + name) if name and name != tag else ""}
  <span style="opacity:.7">· published {escape(published)}</span>
</p>
{summary_html}
<h3>Supported models (added or highlighted in {escape(tag)})</h3>
{vendor_html}
"""


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

    # ---- latest release + supported models ----
    latest_html = _render_latest_release(db_path, repo)

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

        recent = prs[prs["created_at"] >= pd.Timestamp(now) - pd.Timedelta(days=180)].copy()
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
    <a href="reports/">All daily reports</a>
  </nav>
</header>
{cards_html}
{latest_html}
<h2>Trends</h2>
{charts_html}
<footer>Generated by vllm-insights. Data from the GitHub REST API,
cached locally to SQLite, refreshed daily via GitHub Actions.</footer>
</body></html>"""
    out = docs_dir / "index.html"
    out.write_text(body, encoding="utf-8")
    return out


def _wrap_html(title: str, body_html: str, back_href: str = "../") -> str:
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<style>{PAGE_CSS}
article {{ font-size: .95rem; }}
article table {{ border-collapse: collapse; margin: 1rem 0; }}
article th, article td {{ border: 1px solid #ddd5; padding: .35rem .6rem; }}
article code {{ background: #8881; padding: 0 .25rem; border-radius: 3px; }}
article ul {{ padding-left: 1.2rem; }}
</style>
</head><body>
<header><nav><a href="{back_href}">&larr; Home</a></nav><h1>{escape(title)}</h1></header>
<article>{body_html}</article>
</body></html>"""


def build_report_index(reports_dir: Path, title: str) -> Path | None:
    """Render every *.md under reports_dir to a sibling *.html, plus an index.html."""
    import markdown as md  # local import keeps optional-ish

    reports_dir.mkdir(parents=True, exist_ok=True)
    md_files = sorted(
        (p for p in reports_dir.glob("*.md") if p.name != "index.md"),
        reverse=True,
    )
    if not md_files:
        return None

    # Render each .md to .html (same stem)
    for f in md_files:
        html_body = md.markdown(
            f.read_text(encoding="utf-8"),
            extensions=["tables", "fenced_code"],
        )
        (reports_dir / f"{f.stem}.html").write_text(
            _wrap_html(f.stem, html_body), encoding="utf-8"
        )

    # Build index.html
    items = []
    if (reports_dir / "latest.md").exists():
        items.append('<li><a href="latest.html"><strong>Latest</strong></a></li>')
    for f in md_files:
        if f.stem == "latest":
            continue
        items.append(f'<li><a href="{escape(f.stem)}.html">{escape(f.stem)}</a></li>')

    index_html = _wrap_html(title, "<ul>" + "\n".join(items) + "</ul>")
    out = reports_dir / "index.html"
    out.write_text(index_html, encoding="utf-8")
    return out
