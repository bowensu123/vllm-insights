"""Build a static HTML dashboard under docs/ for GitHub Pages.

Audience: vLLM serving engineers and people sizing up vLLM for production.
The page is organised around the decisions those readers actually make:

  1. Upgrade decision for the latest release (LLM-generated verdict)
  2. Capability matrix — what works on which hardware, today
  3. Supported-models compatibility focus — backed by a live mirror of
     `vllm/model_executor/models/registry.py`
  4. Weekly themed digest pointer
  5. Activity stats — demoted into a collapsed details block at the bottom
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
from .capability import CAPABILITY_CSS, render_capability_matrix
from .db import connect
from .models import (
    FOCUS_VENDORS,
    classify as classify_model,
    classify_arch,
    hf_org_url,
    hf_search_url,
    is_focus_vendor,
    looks_like_model_section,
    vendor_tech,
)
from .registry_sync import load_registry
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
.release-summary > summary {
  cursor: pointer;
  font-weight: 600;
  font-size: .85rem;
  text-transform: uppercase;
  letter-spacing: .05em;
  padding: .5rem 0;
  list-style: revert;
  opacity: .8;
}
.release-summary > summary:hover { opacity: 1; }
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

/* Supported-models / vLLM compatibility cards */
.models-intro { font-size: .9rem; opacity: .75; margin: .2rem 0 1rem; }
.vendor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
               gap: .9rem; margin: .6rem 0 1.4rem; }
.vendor-card { border: 1px solid #ddd5; border-radius: 8px; padding: .8rem 1rem;
               background: rgba(127,127,127,.04); display: flex; flex-direction: column; gap: .55rem; }
.vendor-card .vendor-head { display: flex; align-items: baseline; gap: .5rem;
                            flex-wrap: wrap; }
.vendor-card .vendor-name { font-size: 1.05rem; font-weight: 600; }
.vendor-card .vendor-name a { text-decoration: none; }
.vendor-card .vendor-name a:hover { text-decoration: underline; }
.vendor-card .tagline { font-size: .85rem; opacity: .75; margin: 0; }
.vendor-card .row-label { font-size: .68rem; font-weight: 600;
                          text-transform: uppercase; letter-spacing: .08em;
                          opacity: .55; margin-right: .35rem; }
.vendor-card .row { font-size: .8rem; line-height: 1.7; }
.pill { display: inline-block; padding: .05rem .45rem; margin: 0 .2rem .2rem 0;
        border-radius: 10px; border: 1px solid #8884; font-size: .72rem;
        background: rgba(127,127,127,.07); white-space: nowrap; }
.pill.arch { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
             font-size: .68rem; border-color: #6cf6; background: rgba(102,204,255,.08); }
.pill.modal { text-transform: capitalize; border-color: #9c6f; background: rgba(160,120,255,.1); }
.pill.feat  { border-color: #6c96; background: rgba(102,200,150,.08); }
.vendor-card .new-list { margin: .25rem 0 0; padding-left: 1.1rem; font-size: .82rem; }
.vendor-card .new-list li { margin: .15rem 0; }
.vendor-card .no-new { font-size: .78rem; opacity: .55; font-style: italic; margin: 0; }
.vendor-card .series { font-size: .72rem; opacity: .6; }
.vendor-card .pill.arch.removed {
    text-decoration: line-through;
    opacity: .45;
    border-color: #c66a;
    background: rgba(220,80,80,.08);
}
.vendor-card .registry-meta { font-size: .68rem; opacity: .5;
    border-top: 1px dashed #6663; padding-top: .35rem; margin-top: .2rem; }

/* Positioning header + audience line */
.lede { font-size: .95rem; opacity: .85; margin: .4rem 0 .2rem; max-width: 70ch; }
.audience { font-size: .8rem; opacity: .55; margin: 0; }
.section-lede { font-size: .88rem; opacity: .8; margin: .3rem 0 .8rem; max-width: 75ch; }

/* Digest pointer block */
.digest-pointer {
    display: block; padding: .8rem 1rem; margin: 1rem 0 1.5rem;
    border: 1px solid #ddd5; border-radius: 8px;
    background: rgba(127,127,127,.04); text-decoration: none; color: inherit;
}
.digest-pointer:hover { background: rgba(102,204,255,.08); border-color: #6cf8; }
.digest-pointer h3 { margin: 0 0 .25rem; font-size: 1rem; }
.digest-pointer p { margin: 0; font-size: .85rem; opacity: .75; }

/* Activity stats collapsed at the bottom */
details.activity > summary {
    cursor: pointer; font-weight: 600; padding: .6rem 0;
    font-size: 1rem; border-bottom: 1px solid #ddd3;
}
details.activity[open] > summary { margin-bottom: 1rem; }
""" + CAPABILITY_CSS


def _fig_html(fig, div_id: str) -> str:
    return pio.to_html(fig, full_html=False, include_plotlyjs="cdn", div_id=div_id,
                       config={"displaylogo": False})


def _card(value: str, label: str) -> str:
    return f'<div class="card"><div class="v">{escape(value)}</div><div class="l">{escape(label)}</div></div>'


def _item_to_html(item: str, repo: str) -> str:
    """Render a single release-note item: link PR refs and markdown links."""
    html = link_refs(item, repo)
    html = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener">\1</a>',
        html,
    )
    return html


def _load_registry_by_vendor(db_path: Path) -> tuple[
    dict[str, list[dict]], dict[str, list[dict]], str | None
]:
    """Load mirrored upstream registry rows and group them by focus vendor.

    Returns `(live, removed, last_seen_at)` where each dict is
    `{vendor_name: [registry_row, ...]}`. `last_seen_at` is the timestamp of
    the most recent sync that observed any row — useful for a "registry as of"
    footer.
    """
    rows = load_registry(db_path, include_removed=True)
    live: dict[str, list[dict]] = {}
    removed: dict[str, list[dict]] = {}
    last_seen: str | None = None
    for r in rows:
        if r["last_seen_at"] and (last_seen is None or r["last_seen_at"] > last_seen):
            last_seen = r["last_seen_at"]
        hit = classify_arch(r["arch_class"])
        if not hit:
            continue
        vendor, _ = hit
        if not is_focus_vendor(vendor):
            continue
        bucket = removed if r["removed_at"] else live
        bucket.setdefault(vendor, []).append(r)
    return live, removed, last_seen


def _render_focus_grid(
    by_focus: dict[str, list[tuple[str, str]]],
    db_path: Path,
    repo: str,
) -> str:
    """Render a grid of tech cards for the curated focus vendors.

    The arch-class pills now come from the live mirror of upstream
    `registry.py` (synced via `vllm-insights sync --registry`); the curated
    `VENDOR_TECH` table provides only the human-authored tagline, modalities,
    feature pills and series names. If the registry hasn't been synced yet we
    fall back to the curated arch list so the page is never empty.
    """
    live, removed, last_seen = _load_registry_by_vendor(db_path)
    from .models import VENDOR_RULES

    cards: list[str] = []
    for vendor in FOCUS_VENDORS:
        tech = vendor_tech(vendor) or {}
        items = by_focus.get(vendor, [])

        # Vendor display + HF org link
        org_slug = items[0][1] if items else None
        if not org_slug:
            for _, vname, oslug in VENDOR_RULES:
                if vname == vendor:
                    org_slug = oslug
                    break
        if org_slug:
            head = (
                f'<a href="{hf_org_url(org_slug)}" target="_blank" '
                f'rel="noopener">{escape(vendor)}</a>'
            )
        else:
            head = escape(vendor)

        # Arch pills — live registry first, fall back to curated list
        live_archs = [r["arch_class"] for r in live.get(vendor, [])]
        removed_archs = [r["arch_class"] for r in removed.get(vendor, [])]
        if live_archs or removed_archs:
            arch_pills = "".join(
                f'<span class="pill arch">{escape(a)}</span>'
                for a in sorted(live_archs)
            ) + "".join(
                f'<span class="pill arch removed" title="Removed upstream">'
                f'{escape(a)}</span>'
                for a in sorted(removed_archs)
            )
        else:
            arch_pills = "".join(
                f'<span class="pill arch">{escape(a)}</span>'
                for a in tech.get("archs", [])
            )

        modals = "".join(
            f'<span class="pill modal">{escape(m)}</span>' for m in tech.get("modal", [])
        )
        feats = "".join(
            f'<span class="pill feat">{escape(f)}</span>' for f in tech.get("features", [])
        )
        series = tech.get("series") or []
        series_html = (
            f'<div class="series">Series: {escape(" · ".join(series))}</div>'
            if series else ""
        )

        if items:
            lis = []
            for item, _org in items:
                inner = _item_to_html(item, repo)
                hf = (
                    f' <a href="{hf_search_url(item)}" target="_blank" '
                    f'rel="noopener" title="Find on Hugging Face">[HF]</a>'
                )
                lis.append(f"<li>{inner}{hf}</li>")
            new_block = (
                f'<div class="row"><span class="row-label">'
                f'New in this release ({len(items)})</span></div>'
                f'<ul class="new-list">{"".join(lis)}</ul>'
            )
        else:
            new_block = '<p class="no-new">No new entries in this release.</p>'

        arch_count = len(live_archs) if live_archs else len(tech.get("archs", []))
        registry_meta = (
            f'<div class="registry-meta">'
            f'{arch_count} arch{"" if arch_count == 1 else "es"} in vLLM registry'
            + (f' · removed: {len(removed_archs)}' if removed_archs else "")
            + '</div>'
        )

        tagline = tech.get("tagline", "")
        cards.append(
            '<div class="vendor-card">'
            f'<div class="vendor-head"><span class="vendor-name">{head}</span></div>'
            + (f'<p class="tagline">{escape(tagline)}</p>' if tagline else "")
            + (
                f'<div class="row"><span class="row-label">vLLM arch</span>{arch_pills}</div>'
                if arch_pills else ""
            )
            + (
                f'<div class="row"><span class="row-label">Modalities</span>{modals}</div>'
                if modals else ""
            )
            + (
                f'<div class="row"><span class="row-label">Engine features</span>{feats}</div>'
                if feats else ""
            )
            + series_html
            + new_block
            + registry_meta
            + "</div>"
        )

    footer = ""
    if last_seen:
        footer = (
            f'<p style="font-size:.72rem;opacity:.55;margin:.3rem 0 0">'
            f'Architecture pills mirror upstream '
            f'<code>vllm/model_executor/models/registry.py</code> '
            f'as of {escape(last_seen[:16].replace("T", " "))} UTC.</p>'
        )

    return '<div class="vendor-grid">' + "\n".join(cards) + "</div>" + footer


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

    # Group items from model-related sections by detected vendor. We only
    # surface entries that belong to one of the curated focus vendors
    # (Qwen / DeepSeek / MiniMax / GLM / Meta / Google / Microsoft); everything
    # else from the release notes is intentionally dropped from this section.
    by_focus: dict[str, list[tuple[str, str]]] = {}
    for s in sections:
        if not looks_like_model_section(s["section"]):
            continue
        cls = classify_model(s["item"])
        if not cls:
            continue
        vendor, org = cls
        if is_focus_vendor(vendor):
            by_focus.setdefault(vendor, []).append((s["item"], org))

    vendor_html = _render_focus_grid(by_focus, db_path, repo)

    published = latest["published_at"][:10] if latest.get("published_at") else "?"

    summary_html = ""
    if summary_row:
        rendered = md.markdown(summary_row["summary"], extensions=["tables", "fenced_code"])
        meta = (
            f"<span class='meta'>LLM summary · "
            f"{escape(summary_row['backend'] or '?')} / "
            f"{escape(summary_row['model'] or '?')}</span>"
        )
        summary_html = (
            "<details open class='release-summary'>"
            "<summary>Upgrade verdict (LLM-generated)</summary>"
            f"{rendered}{meta}"
            "</details>"
        )

    return f"""
<h2>Should you upgrade to {escape(tag)}?</h2>
<p>
  <a href="{escape(rel_url)}" target="_blank" rel="noopener"><strong>{escape(tag)}</strong></a>
  {escape("— " + name) if name and name != tag else ""}
  <span style="opacity:.7">· published {escape(published)}</span>
</p>
<p class="section-lede">
  The verdict below is generated from the raw release notes by an LLM and answers
  the only question that matters for an operator: should you upgrade, wait, or
  skip — and what will break if you do? Treat it as a first pass, not a guarantee;
  cross-check the linked release notes before rolling to production.
</p>
{summary_html}
<h3>Supported models &mdash; vLLM compatibility focus</h3>
<p class="models-intro">
  Architecture-class pills are mirrored from upstream
  <code>vllm/model_executor/models/registry.py</code> on every sync, so they
  stay correct as new models land or get dropped. Modalities, engine-feature
  and series labels are curated. New entries from {escape(tag)} are highlighted
  inline. We surface seven families: Qwen / DeepSeek / MiniMax / GLM and the US
  top-3 open-source families (Llama / Gemma / Phi).
</p>
{vendor_html}
"""


def _render_digest_pointer(docs_dir: Path) -> str:
    """If a weekly digest exists, link to it from the homepage."""
    weekly = docs_dir / "weekly" / "latest.html"
    if not weekly.exists():
        # The HTML version is built by `build_report_index`. If we don't have
        # the HTML yet but do have the md, still link out so the page is useful.
        weekly_md = docs_dir / "weekly" / "latest.md"
        if not weekly_md.exists():
            return ""
    return (
        '<a class="digest-pointer" href="weekly/latest.html">'
        '<h3>This week in vLLM &rarr;</h3>'
        '<p>Theme-sliced digest: Kernels &amp; attention, Quantization, '
        'Parallelism &amp; scheduling, Model support, Hardware, API &amp; serving, '
        'Watch list. Generated weekly from merged PRs + releases.</p>'
        '</a>'
    )


def _render_activity(rel: pd.DataFrame, prs: pd.DataFrame, cm: pd.DataFrame,
                     now: datetime) -> str:
    """Activity / vanity stats, collapsed behind a details element.

    These charts (release cadence, merge time, PRs per month, top committers)
    used to dominate the homepage. They're useful but they don't answer any
    operator question and they make the page look like a generic GitHub
    dashboard, so we tuck them away.
    """
    cards: list[str] = []
    cards.append(_card(str(len(rel)), "Releases tracked"))
    if not rel.empty:
        med = rel["interval_days"].dropna().median()
        cards.append(_card(f"{med:.1f}d" if pd.notna(med) else "—",
                           "Median release interval"))
    cards.append(_card(str(len(prs)), "PRs in cache"))
    if not prs.empty:
        merged = prs.dropna(subset=["merged_at"])
        med_h = merged["merge_hours"].dropna().median()
        cards.append(_card(f"{med_h:.1f}h" if pd.notna(med_h) else "—",
                           "Median merge time"))
    cards.append(_card(str(len(cm)), "Commits in cache"))
    cards_html = '<div class="cards">' + "".join(cards) + "</div>"

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

    charts_html = '\n'.join(f'<div class="chart">{c}</div>' for c in charts) \
        or '<p><em>No data yet — run <code>vllm-insights sync --all</code> first.</em></p>'

    return (
        '<details class="activity">'
        '<summary>Repo activity stats (vanity metrics — for the curious)</summary>'
        f'{cards_html}{charts_html}'
        '</details>'
    )


def build_index(db_path: Path, docs_dir: Path, repo: str) -> Path:
    docs_dir.mkdir(parents=True, exist_ok=True)
    rel = releases_df(db_path)
    prs = prs_df(db_path)
    cm = commits_df(db_path)
    now = datetime.now(timezone.utc)

    latest_html = _render_latest_release(db_path, repo)
    capability_html = render_capability_matrix()
    digest_html = _render_digest_pointer(docs_dir)
    activity_html = _render_activity(rel, prs, cm, now)

    repo_url = f"https://github.com/{repo}"
    body = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>vLLM Insights — capability &amp; release intelligence</title>
<style>{PAGE_CSS}</style>
</head><body>
<header>
  <h1>vLLM Insights</h1>
  <p class="lede">
    Capability matrix and release intelligence for
    <a href="{repo_url}">{escape(repo)}</a>.
    Built for engineers picking a vLLM version, sizing up a serving rig, or
    deciding whether a model family is actually production-ready.
  </p>
  <p class="audience">
    Updated {now:%Y-%m-%d %H:%M UTC} · data: GitHub REST · supported-models: mirrored from
    upstream <code>registry.py</code>
  </p>
  <nav style="margin-top:.6rem">
    <a href="weekly/">Weekly digest</a>
    <a href="reports/">Daily archive</a>
  </nav>
</header>
{latest_html}
{capability_html}
{digest_html}
{activity_html}
<footer>Generated by vllm-insights. GitHub data cached to SQLite and refreshed
every 6 hours; capability matrix is curated and reviewed manually; supported-model
arch pills are mirrored verbatim from upstream <code>vllm/model_executor/models/registry.py</code>.</footer>
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
