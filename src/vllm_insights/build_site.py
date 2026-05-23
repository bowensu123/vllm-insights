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

from .analysis.history import counts_over_time
from .analysis.perf_claims import recent_claims
from .analysis.pr_issue_links import top_issue_hotspots
from .analysis.release_diff import latest_pair, load_drift_for_pair
from .analysis.social import hottest_recent_prs, recent_hn_mentions, top_hn_mentions
from .analysis.topics import (
    cluster_for_pr, cluster_momentum, load_top_clusters,
)
from .analysis.benchmarks import load_recent_benchmarks
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
    vendor_meta,
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
.vendor-card .pill.arch.removed {
    text-decoration: line-through;
    opacity: .45;
    border-color: #c66a;
    background: rgba(220,80,80,.08);
}
.vendor-card .arch-list { display: flex; flex-direction: column; gap: .4rem; }
.vendor-card .arch-group { display: block; }
.vendor-card .arch-cat { font-size: .65rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: .06em; opacity: .55;
    margin-right: .45rem; }
.vendor-card .arch-cat.removed-cat { color: #c66; opacity: .8; }
.vendor-card .vendor-activity { font-size: .78rem;
    border-top: 1px dashed #6663; padding-top: .4rem; }
.vendor-card .vendor-activity .row-label { display: block;
    margin-bottom: .15rem; }
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

/* Forks */
section.forks { margin: 2rem 0 1rem; }
ul.fork-list { list-style: none; padding: 0; }
ul.fork-list > li { padding: .55rem 0; border-bottom: 1px solid #ddd3; font-size: .9rem; }
ul.fork-list > li:last-child { border-bottom: 0; }
.fork-meta { font-size: .72rem; opacity: .65; margin-left: .4rem; }
ul.fork-commits { margin: .35rem 0 .1rem 1rem; padding-left: .8rem;
    border-left: 2px solid #6cf4; font-size: .78rem; }
ul.fork-commits li { padding: .15rem 0; opacity: .85; }
ul.fork-commits code { font-size: .72rem; opacity: .9; }
.fork-c-meta { opacity: .55; font-size: .68rem; }

/* Discovered topics */
section.topics { margin: 2rem 0 1rem; }
section.topics h3 { margin-top: 1rem; font-size: .95rem; opacity: .8;
    text-transform: uppercase; letter-spacing: .05em; }
.topic-grid { display: flex; flex-wrap: wrap; gap: .4rem; margin: .4rem 0 .8rem; }
.topic-pill { padding: .35rem .7rem; border-radius: 12px;
    border: 1px solid #6cf6; background: rgba(102,204,255,.07);
    display: flex; flex-direction: column; gap: .1rem; min-width: 110px; }
.topic-label { font-size: .82rem; font-weight: 600; }
.topic-size { font-size: .68rem; opacity: .7; }

/* Issue hotspots */
section.hotspots { margin: 2rem 0 1rem; }
ul.hotspot-list { list-style: none; padding: 0; }
ul.hotspot-list li { padding: .35rem 0; border-bottom: 1px solid #ddd3;
    font-size: .88rem; }
ul.hotspot-list a { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    text-decoration: none; opacity: .85; }
ul.hotspot-list a:hover { opacity: 1; text-decoration: underline; }
.hot-count { font-size: .7rem; opacity: .7; margin-left: .4rem;
    padding: .02rem .35rem; border-radius: 4px;
    background: rgba(255,170,40,.12); border: 1px solid #b8862b66;
    color: #b8862b; }

/* Release drift */
section.drift { margin: 2rem 0 1rem; }
table.drift-table { border-collapse: collapse; width: 100%; font-size: .85rem;
    margin-top: .4rem; }
table.drift-table th, table.drift-table td {
    padding: .35rem .55rem; border-bottom: 1px solid #ddd3;
    text-align: left; vertical-align: middle;
}
table.drift-table th { font-size: .72rem; text-transform: uppercase;
    letter-spacing: .04em; opacity: .8; }
table.drift-table td.dir code { font-size: .78rem; }
table.drift-table td.files { width: 5rem; text-align: right; opacity: .8; }
table.drift-table td.changes { font-size: .78rem; position: relative; }
.changes-bar { height: 3px; background: linear-gradient(90deg, #6c9 0%, #b85 100%);
    margin-top: .25rem; border-radius: 2px; }

/* Perf claims (author-asserted deltas) */
section.perf-claims { margin: 2rem 0 1rem; }
ul.claims-list { list-style: none; padding: 0; }
ul.claims-list li { padding: .35rem 0; border-bottom: 1px solid #ddd3;
    font-size: .88rem; display: flex; flex-wrap: wrap; align-items: baseline;
    gap: .35rem; }
.claim-snip { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .82rem; color: #2c8f48; font-weight: 600; }
.claim-tag { padding: .02rem .35rem; border-radius: 4px; font-size: .68rem;
    border: 1px solid #8884; opacity: .85; }
.claim-tag.hw { background: rgba(102,204,255,.1); border-color: #6cf6; }
.claim-tag.model { background: rgba(160,120,255,.1); border-color: #9c6f; }
section.perf-claims .footnote { font-size: .72rem; opacity: .55;
    margin: .6rem 0 0; }

/* Growth-over-time charts */
section.trends { margin: 2rem 0 1rem; }
section.trends .chart { margin: .8rem 0; }

/* Topic momentum */
section.momentum { margin: 2rem 0 1rem; }
.momentum-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 700px) { .momentum-grid { grid-template-columns: 1fr; } }
.momentum-col h3 { font-size: .95rem; margin: .3rem 0 .4rem;
    text-transform: uppercase; letter-spacing: .04em; opacity: .75; }
.momentum-col ul { list-style: none; padding: 0; margin: 0; }
.momentum-col li { display: flex; justify-content: space-between;
    padding: .3rem 0; border-bottom: 1px solid #ddd3; font-size: .85rem; }
.momentum-col li:last-child { border-bottom: 0; }
.momentum-col .topic-label { font-weight: 500; }
.momentum-col .momentum.up   { color: #2c8f48; font-size: .8rem; font-family: ui-monospace, Menlo, monospace; }
.momentum-col .momentum.down { color: #b85; font-size: .8rem; font-family: ui-monospace, Menlo, monospace; }
.momentum-col .momentum .ratio { opacity: .75; font-weight: 600; margin-left: .3rem; }

/* Community temperature */
section.social { margin: 2rem 0 1rem; }
section.social h3 { font-size: .95rem; margin-top: 1rem;
    text-transform: uppercase; letter-spacing: .04em; opacity: .75; }
ul.hot-prs, ul.hn-list { list-style: none; padding: 0; }
ul.hot-prs li, ul.hn-list li { padding: .35rem 0; border-bottom: 1px solid #ddd3;
    font-size: .85rem; display: flex; flex-wrap: wrap; align-items: baseline;
    gap: .4rem; }
.react-total { font-weight: 700; font-size: .85rem; min-width: 2rem;
    color: #b8862b; }
.react-em { font-size: .78rem; opacity: .8; font-family: -apple-system, sans-serif; }
.hn-points { font-weight: 700; color: #ff6600; min-width: 3rem; font-size: .85rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.hn-meta { font-size: .72rem; opacity: .65; margin-left: .35rem; }
.hn-meta a { color: inherit; }

/* Benchmarks */
section.benchmarks { margin: 2rem 0 1rem; }
table.bench-table { border-collapse: collapse; width: 100%; font-size: .82rem;
    margin-top: .4rem; }
table.bench-table th, table.bench-table td {
    padding: .3rem .5rem; border-bottom: 1px solid #ddd3; text-align: left;
}
table.bench-table th.num, table.bench-table td.num { text-align: right;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
table.bench-table td.obs { font-size: .72rem; opacity: .7;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }

/* Open issues block */
section.open-issues { margin: 2rem 0 1rem; }
section.open-issues h2 { margin-bottom: .3rem; }
ul.issue-list { list-style: none; padding: 0; margin: .4rem 0; }
ul.issue-list li { padding: .35rem 0; border-bottom: 1px solid #ddd3;
    font-size: .88rem; }
ul.issue-list li:last-child { border-bottom: 0; }
ul.issue-list li a { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    text-decoration: none; opacity: .85; }
ul.issue-list li a:hover { opacity: 1; text-decoration: underline; }
.issue-label { display: inline-block; font-size: .68rem;
    padding: .02rem .35rem; margin-left: .2rem; border-radius: 6px;
    border: 1px solid #8884; background: rgba(127,127,127,.07);
    opacity: .8; }
.issue-meta { font-size: .72rem; opacity: .55; margin-left: .4rem; }

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
    dict[str, dict[str, list[dict]]], dict[str, list[dict]], str | None
]:
    """Load mirrored upstream registry rows and group by focus vendor and
    registry category (text / multimodal / embedding / …).

    Returns `(live, removed, last_seen_at)` where:
      live[vendor][category] = [registry_row, ...]
      removed[vendor]        = [registry_row, ...]  (no category breakdown
                                                     because the row is
                                                     historical anyway)
    """
    rows = load_registry(db_path, include_removed=True)
    live: dict[str, dict[str, list[dict]]] = {}
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
        if r["removed_at"]:
            removed.setdefault(vendor, []).append(r)
        else:
            live.setdefault(vendor, {}).setdefault(r["category"], []).append(r)
    return live, removed, last_seen


def _vendor_activity_90d(db_path: Path, modules: list[str]) -> tuple[int, str | None]:
    """Count merged PRs from the last 90 days that touched any file path under
    `vllm/model_executor/models/{module}*` for the given module names. Returns
    `(count, most_recent_merge_at)`.
    """
    if not modules:
        return 0, None
    placeholders = " OR ".join(["prf.path LIKE ?"] * len(modules))
    args = [f"vllm/model_executor/models/{m}%" for m in modules]
    with connect(db_path) as conn:
        row = conn.execute(
            f"""
            SELECT COUNT(DISTINCT p.number) AS n, MAX(p.merged_at) AS last_at
            FROM pull_requests p
            JOIN pr_files prf ON prf.pr_number = p.number
            WHERE p.merged_at IS NOT NULL
              AND p.merged_at >= datetime('now', '-90 days')
              AND ({placeholders})
            """,
            tuple(args),
        ).fetchone()
    return int(row["n"] or 0), row["last_at"]


# Registry category → user-facing modality label. This is derivation, not
# curation: the category is upstream's own grouping.
_CATEGORY_LABEL = {
    "text":             "text-generation",
    "multimodal":       "multimodal",
    "embedding":        "embedding",
    "classification":   "classification",
    "speculative":      "draft (spec-decode)",
    "reward":           "reward",
    "late_interaction": "retrieval",
    "transcription":    "transcription",
    "cross_encoder":    "cross-encoder",
}


def _render_focus_grid(
    by_focus: dict[str, list[tuple[str, str]]],
    db_path: Path,
    repo: str,
) -> str:
    """Render the focus-vendor grid.

    Everything in each card is derived: arches come from the live mirror of
    upstream `registry.py`, category buckets are upstream's own grouping,
    PR activity is computed from our pr_files cache. The only hardcoded thing
    we keep is the HF org slug (a permanent URL anchor — there's no honest way
    to derive it).
    """
    live, removed, last_seen = _load_registry_by_vendor(db_path)

    cards: list[str] = []
    for vendor in FOCUS_VENDORS:
        meta = vendor_meta(vendor) or {}
        org_slug = meta.get("hf_org")
        head = (
            f'<a href="{hf_org_url(org_slug)}" target="_blank" '
            f'rel="noopener">{escape(vendor)}</a>'
            if org_slug else escape(vendor)
        )

        live_by_cat = live.get(vendor, {})
        removed_archs = [r["arch_class"] for r in removed.get(vendor, [])]
        all_live = [r for cat in live_by_cat.values() for r in cat]
        total = len(all_live)

        # One "modality" badge per registry category we have arches in. The
        # set of categories is sourced from upstream, not from my head.
        cat_pills = "".join(
            f'<span class="pill modal">{escape(_CATEGORY_LABEL.get(cat, cat))}'
            f' &times;{len(arches)}</span>'
            for cat, arches in sorted(live_by_cat.items(), key=lambda kv: -len(kv[1]))
        )

        # Arch pills — every live arch, in alphabetical order, grouped visually
        # by category (we show category as a thin label between groups).
        arch_blocks: list[str] = []
        for cat, arches in sorted(live_by_cat.items(), key=lambda kv: -len(kv[1])):
            pills = "".join(
                f'<span class="pill arch">{escape(a["arch_class"])}</span>'
                for a in sorted(arches, key=lambda a: a["arch_class"])
            )
            arch_blocks.append(
                f'<div class="arch-group">'
                f'<span class="arch-cat">{escape(_CATEGORY_LABEL.get(cat, cat))}</span>'
                f'{pills}</div>'
            )
        if removed_archs:
            pills = "".join(
                f'<span class="pill arch removed" title="No longer in upstream registry">'
                f'{escape(a)}</span>'
                for a in sorted(removed_archs)
            )
            arch_blocks.append(
                '<div class="arch-group">'
                '<span class="arch-cat removed-cat">removed upstream</span>'
                f'{pills}</div>'
            )

        # Recent activity: PR touches under any module owned by this vendor's
        # arches. Module names are taken from `module_name` in the registry row
        # — that's the actual import path upstream uses, not something we made
        # up.
        modules = sorted({a["module_name"] for a in all_live if a.get("module_name")})
        pr_count_90d, last_pr = _vendor_activity_90d(db_path, modules)
        last_pr_short = last_pr[:10] if last_pr else None
        activity_class = (
            "act-hot" if pr_count_90d >= 6 else
            "act-warm" if pr_count_90d >= 1 else "act-cold"
        )
        activity_html = (
            f'<div class="vendor-activity">'
            f'<span class="row-label">Recent activity</span>'
            f'<span class="{activity_class}">{pr_count_90d} PR(s) in last 90d</span>'
            + (f' &middot; last merge {escape(last_pr_short)}' if last_pr_short else "")
            + '</div>'
        )

        # "New in current release" from release notes — kept because it's the
        # only thing that connects this card to the latest release.
        items = by_focus.get(vendor, [])
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

        registry_meta = (
            f'<div class="registry-meta">'
            f'{total} live arch{"" if total == 1 else "es"} in vLLM registry'
            + (f' &middot; {len(removed_archs)} removed' if removed_archs else "")
            + '</div>'
        )

        cards.append(
            '<div class="vendor-card">'
            f'<div class="vendor-head"><span class="vendor-name">{head}</span></div>'
            + (
                f'<div class="row"><span class="row-label">Categories</span>{cat_pills}</div>'
                if cat_pills else ""
            )
            + ('<div class="arch-list">' + "".join(arch_blocks) + '</div>' if arch_blocks else "")
            + activity_html
            + new_block
            + registry_meta
            + "</div>"
        )

    footer = ""
    if last_seen:
        footer = (
            f'<p style="font-size:.72rem;opacity:.55;margin:.3rem 0 0">'
            f'Architecture pills, categories and counts are mirrored from upstream '
            f'<code>vllm/model_executor/models/registry.py</code> '
            f'as of {escape(last_seen[:16].replace("T", " "))} UTC. '
            f'Activity counts come from the merged-PR cache.</p>'
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
<h2>Latest release &mdash; {escape(tag)}</h2>
<p>
  <a href="{escape(rel_url)}" target="_blank" rel="noopener"><strong>{escape(tag)}</strong></a>
  {escape("— " + name) if name and name != tag else ""}
  <span style="opacity:.7">· published {escape(published)}</span>
</p>
{summary_html}
<h3>Supported models</h3>
{vendor_html}
"""


def _render_open_issues(db_path: Path) -> str:
    """Top open issues across the labels we care about (performance,
    regression, RFC, hardware bugs, release-blocker). Pulled from the
    `issues` table — empty if the issues sync hasn't run yet.
    """
    with connect(db_path) as conn:
        # Check if the table has anything before we render the section header.
        any_row = conn.execute("SELECT 1 FROM issues LIMIT 1").fetchone()
        if not any_row:
            return ""
        rows = conn.execute(
            """SELECT number, title, labels, url, comments, updated_at
               FROM issues
               WHERE state = 'OPEN'
               ORDER BY
                 -- prioritise release-blocker and regression labels
                 CASE
                   WHEN labels LIKE '%release-blocker%' THEN 0
                   WHEN labels LIKE '%regression%' THEN 1
                   WHEN labels LIKE '%performance%' THEN 2
                   WHEN labels LIKE '%RFC%' OR labels LIKE '%rfc%' THEN 3
                   ELSE 4
                 END,
                 updated_at DESC
               LIMIT 20"""
        ).fetchall()

    if not rows:
        return ""

    items = []
    for r in rows:
        lbls = [l.strip() for l in (r["labels"] or "").split(",") if l.strip()]
        # Show only the labels we care about so the row doesn't drown in noise.
        keep = [l for l in lbls if any(
            kw in l.lower() for kw in
            ("performance", "regression", "rfc", "blocker", "hardware",
             "rocm", "tpu", "cpu", "correctness")
        )]
        label_html = " ".join(
            f'<span class="issue-label">{escape(l)}</span>' for l in keep[:4]
        )
        last = (r["updated_at"] or "")[:10]
        items.append(
            f'<li>'
            f'<a href="{r["url"]}" target="_blank" rel="noopener">'
            f'#{r["number"]}</a> {escape(r["title"])} {label_html} '
            f'<span class="issue-meta">{escape(last)} &middot; '
            f'{r["comments"] or 0} comment{"" if (r["comments"] or 0) == 1 else "s"}</span>'
            f'</li>'
        )

    return (
        '<section class="open-issues">'
        '<h2>Open issues worth watching</h2>'
        f'<ul class="issue-list">{"".join(items)}</ul>'
        '</section>'
    )


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


def _render_forks(db_path: Path) -> str:
    """Top forks by ahead_by (the ones carrying actual independent work)."""
    with connect(db_path) as conn:
        any_row = conn.execute("SELECT 1 FROM forks LIMIT 1").fetchone()
        if not any_row:
            return ""
        rows = conn.execute(
            """SELECT full_name, stars, ahead_by, behind_by, pushed_at, url
               FROM forks WHERE ahead_by > 0
               ORDER BY ahead_by DESC LIMIT 12"""
        ).fetchall()
        if not rows:
            return ""
        # Pull sample commits for the top 3 forks
        sample_commits: dict[str, list[dict]] = {}
        for r in rows[:3]:
            commits = conn.execute(
                """SELECT sha, message, author, committed_at, url
                   FROM fork_commits WHERE fork_full_name = ?
                   ORDER BY committed_at DESC LIMIT 5""",
                (r["full_name"],),
            ).fetchall()
            sample_commits[r["full_name"]] = [dict(c) for c in commits]

    items = []
    for r in rows:
        commits_html = ""
        if sample_commits.get(r["full_name"]):
            cs = "".join(
                f"<li><a href='{escape(c['url'] or '')}' target='_blank' rel='noopener'>"
                f"<code>{escape((c['sha'] or '')[:7])}</code></a> "
                f"{escape((c['message'] or '')[:120])}"
                f"<span class='fork-c-meta'> &middot; @{escape(c['author'] or '?')}</span></li>"
                for c in sample_commits[r["full_name"]]
            )
            commits_html = f"<ul class='fork-commits'>{cs}</ul>"
        last_push = (r["pushed_at"] or "")[:10]
        items.append(
            "<li>"
            f"<a href='{escape(r['url'] or '')}' target='_blank' rel='noopener'>"
            f"<strong>{escape(r['full_name'])}</strong></a> "
            f"<span class='fork-meta'>"
            f"{r['stars']}★ · ahead {r['ahead_by']} / behind {r['behind_by']} · "
            f"last push {escape(last_push)}"
            f"</span>"
            f"{commits_html}"
            "</li>"
        )
    return (
        '<section class="forks">'
        '<h2>Active forks</h2>'
        f'<ul class="fork-list">{"".join(items)}</ul>'
        '</section>'
    )


def _render_topics(db_path: Path) -> str:
    """Top discovered PR topics from the most recent clustering run."""
    pr_top = load_top_clusters(db_path, "pr", top=12)
    issue_top = load_top_clusters(db_path, "issue", top=8)
    if not pr_top and not issue_top:
        return ""

    pr_html = ""
    if pr_top:
        pr_html = (
            "<h3>PR topics</h3><div class='topic-grid'>"
            + "".join(
                f"<div class='topic-pill'>"
                f"<span class='topic-label'>{escape(t['label'])}</span>"
                f"<span class='topic-size'>{t['size']} PRs</span>"
                f"</div>"
                for t in pr_top
            )
            + "</div>"
        )
    issue_html = ""
    if issue_top:
        issue_html = (
            "<h3>Issue topics</h3><div class='topic-grid'>"
            + "".join(
                f"<div class='topic-pill'>"
                f"<span class='topic-label'>{escape(t['label'])}</span>"
                f"<span class='topic-size'>{t['size']} issues</span>"
                f"</div>"
                for t in issue_top
            )
            + "</div>"
        )
    return (
        '<section class="topics">'
        '<h2>Discovered topics</h2>'
        f'{pr_html}{issue_html}'
        '</section>'
    )


def _render_issue_hotspots(db_path: Path) -> str:
    """Open issues most frequently referenced by Fixes/Closes/Resolves PRs."""
    rows = top_issue_hotspots(db_path, limit=12, only_open=True)
    if not rows:
        return ""
    items = []
    for r in rows:
        items.append(
            f"<li>"
            f"<a href='{escape(r['url'] or '')}' target='_blank' rel='noopener'>"
            f"#{r['number']}</a> {escape(r['title'])} "
            f"<span class='hot-count'>{r['pr_count']} PR{'s' if r['pr_count'] != 1 else ''} "
            f"linked</span>"
            f"</li>"
        )
    return (
        '<section class="hotspots">'
        '<h2>Issue hotspots</h2>'
        f'<ul class="hotspot-list">{"".join(items)}</ul>'
        '</section>'
    )


def _render_release_drift(db_path: Path) -> str:
    """Drift heatmap-table for the most recent release pair."""
    pair = latest_pair(db_path)
    if not pair:
        return ""
    from_tag, to_tag = pair
    rows = load_drift_for_pair(db_path, from_tag, to_tag, top=15)
    if not rows:
        return ""
    # Render a simple table; the magnitude column uses a bar to draw the eye.
    max_changes = max((r["additions"] + r["deletions"]) for r in rows) or 1
    body = "".join(
        f"<tr>"
        f"<td class='dir'><code>{escape(r['dir'])}</code></td>"
        f"<td class='files'>{r['files']}</td>"
        f"<td class='changes'>"
        f"+{r['additions']} / -{r['deletions']}"
        f"<div class='changes-bar' style='width:"
        f"{((r['additions'] + r['deletions']) / max_changes * 100):.0f}%'></div>"
        f"</td>"
        f"</tr>"
        for r in rows
    )
    return (
        '<section class="drift">'
        f'<h2>Where the code moved: <code>{escape(from_tag)}</code> &rarr; '
        f'<code>{escape(to_tag)}</code></h2>'
        "<table class='drift-table'>"
        "<thead><tr><th>Directory</th><th>Files</th><th>Lines changed</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
        '</section>'
    )


def _render_benchmarks(db_path: Path) -> str:
    """Recent benchmark observations, if we managed to scrape any."""
    rows = load_recent_benchmarks(db_path, limit=80)
    if not rows:
        return ""
    # Group by (workload, metric, hardware); show latest value
    by_key: dict[tuple[str, str, str], dict] = {}
    for r in rows:
        key = (r["workload"], r["metric"], r["hardware"])
        prev = by_key.get(key)
        if not prev or r["observed_at"] > prev["observed_at"]:
            by_key[key] = r
    items = sorted(by_key.values(),
                   key=lambda r: (r["workload"], r["metric"], r["hardware"]))[:30]
    if not items:
        return ""
    body = "".join(
        f"<tr>"
        f"<td><code>{escape(r['workload'])}</code></td>"
        f"<td><code>{escape(r['hardware'])}</code></td>"
        f"<td>{escape(r['metric'])}</td>"
        f"<td class='num'>{r['value']:.2f}</td>"
        f"<td class='obs'>{escape((r['observed_at'] or '')[:10])}</td>"
        f"</tr>"
        for r in items
    )
    return (
        '<section class="benchmarks">'
        '<h2>Performance signals</h2>'
        "<table class='bench-table'>"
        "<thead><tr><th>Workload</th><th>Hardware</th><th>Metric</th>"
        "<th class='num'>Value</th><th>Observed</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
        '</section>'
    )


def _render_timeseries(db_path: Path, prs: pd.DataFrame) -> str:
    """Time-series charts derived from historical_inventory + pull_requests.

    Four curves, each tied to data we actually have:
      1. Architectures over time   (from historical_inventory, kind='arch')
      2. Quant methods over time   (from historical_inventory, kind='quantization')
      3. Hardware platforms over time (kind='platform')
      4. MoE PR share by month     (from PR titles regex)

    If historical_inventory is empty (history sync hasn't run yet) we skip
    the per-release curves and just show the PR-derived chart.
    """
    charts: list[str] = []

    for kind, label in (
        ("arch", "Supported architectures over time"),
        ("quantization", "Quantization methods per release"),
        ("attention", "Attention backends per release"),
        ("platform", "Hardware platforms per release"),
        ("spec_decode", "Speculative-decoding methods per release"),
    ):
        rows = counts_over_time(db_path, kind)
        if len(rows) < 2:
            continue
        df = pd.DataFrame(rows)
        df["published_at"] = pd.to_datetime(df["published_at"])
        df = df.sort_values("published_at")
        fig = px.line(df, x="published_at", y="n", hover_data=["snapshot_tag"],
                      markers=True, title=label)
        fig.update_layout(yaxis_title="count", xaxis_title="release date")
        charts.append(_fig_html(fig, f"chart-history-{kind}"))

    # MoE PR share by month — purely from cached PRs, doesn't need history.
    if not prs.empty:
        v = prs.dropna(subset=["merged_at"]).copy()
        if not v.empty:
            v["month"] = v["merged_at"].dt.to_period("M").astype(str)
            v["is_moe"] = v["title"].str.contains(
                r"\b(?:moe|expert[- ]parallel|deepep)\b", case=False, regex=True
            ).fillna(False)
            monthly = (
                v.groupby("month")
                .agg(total=("number", "count"),
                     moe=("is_moe", "sum"))
                .reset_index()
            )
            monthly["share_pct"] = (monthly["moe"] / monthly["total"] * 100).round(2)
            # Trim to last 24 months — older data is noisy
            monthly = monthly.tail(24)
            fig = px.bar(monthly, x="month", y="share_pct",
                         title="MoE-related PR share by month (%)",
                         hover_data=["moe", "total"])
            fig.update_layout(yaxis_title="% of monthly PRs",
                              xaxis_title=None)
            charts.append(_fig_html(fig, "chart-moe-share"))

    if not charts:
        return ""
    return (
        '<section class="trends">'
        '<h2>Growth over time</h2>'
        + "\n".join(f'<div class="chart">{c}</div>' for c in charts) +
        '</section>'
    )


def _render_topic_momentum(db_path: Path) -> str:
    """Top growing / shrinking clusters this month vs last."""
    rows = cluster_momentum(db_path, "pr", window_days=30)
    if not rows:
        return ""
    growing = [r for r in rows if r["ratio"] > 1.0 and r["current"] >= 2][:6]
    shrinking = list(reversed(
        [r for r in rows if r["ratio"] < 1.0 and r["previous"] >= 2]
    ))[:6]
    if not growing and not shrinking:
        return ""

    def _block(title: str, items: list[dict], delta_class: str) -> str:
        if not items:
            return ""
        lis = "".join(
            f'<li><span class="topic-label">{escape(r["label"])}</span>'
            f'<span class="momentum {delta_class}">'
            f'{r["current"]} ← {r["previous"]} '
            f'<span class="ratio">×{r["ratio"]:.1f}</span></span></li>'
            for r in items
        )
        return f'<div class="momentum-col"><h3>{title}</h3><ul>{lis}</ul></div>'

    return (
        '<section class="momentum">'
        '<h2>Topic momentum (30d vs prior 30d)</h2>'
        '<div class="momentum-grid">'
        + _block("Heating up", growing, "up")
        + _block("Cooling down", shrinking, "down")
        + '</div></section>'
    )


def _render_perf_claims(db_path: Path) -> str:
    """Author-claimed perf deltas from PR titles + bodies."""
    rows = recent_claims(db_path, limit=20)
    if not rows:
        return ""
    items = []
    for r in rows:
        hw = (f'<span class="claim-tag hw">{escape(r["hardware"])}</span>'
              if r["hardware"] else "")
        model = (f'<span class="claim-tag model">{escape(r["model_hint"])}</span>'
                 if r["model_hint"] else "")
        items.append(
            f'<li>'
            f'<span class="claim-snip">{escape(r["snippet"])}</span>'
            f'{hw}{model}'
            f' &middot; <a href="{escape(r["pr_url"] or "")}" target="_blank" '
            f'rel="noopener">#{r["pr_number"]}</a> '
            f'{escape((r["pr_title"] or "")[:80])}'
            f'</li>'
        )
    return (
        '<section class="perf-claims">'
        '<h2>Perf claims by PR authors</h2>'
        f'<ul class="claims-list">{"".join(items)}</ul>'
        '<p class="footnote">Self-reported deltas extracted from PR titles and '
        'bodies. Verify by clicking through. Canonical perf data lives at '
        '<a href="https://perf.vllm.ai/" target="_blank" rel="noopener">perf.vllm.ai</a>.'
        '</p>'
        '</section>'
    )


def _render_social(db_path: Path) -> str:
    """PR reactions + HN aggregation."""
    hot = hottest_recent_prs(db_path, days=30, limit=8)
    hn = recent_hn_mentions(db_path, limit=8)
    if not hot and not hn:
        return ""
    parts = ['<section class="social"><h2>Community temperature</h2>']
    if hot:
        items = []
        for r in hot:
            ups = r.get("reactions_plus_one") or 0
            rocket = r.get("reactions_rocket") or 0
            heart = r.get("reactions_heart") or 0
            hooray = r.get("reactions_hooray") or 0
            total = r.get("reactions_total") or 0
            items.append(
                f'<li>'
                f'<span class="react-total">{total}</span> '
                f'<span class="react-em">👍{ups} 🚀{rocket} ❤️{heart} 🎉{hooray}</span> '
                f'<a href="{escape(r["url"] or "")}" target="_blank" rel="noopener">'
                f'#{r["number"]}</a> {escape((r["title"] or "")[:90])}'
                f'</li>'
            )
        parts.append(
            "<h3>Most-reacted PRs in 30d</h3>"
            f"<ul class='hot-prs'>{''.join(items)}</ul>"
        )
    if hn:
        items = []
        for r in hn:
            href = r["url"] or r["hn_url"]
            items.append(
                f'<li>'
                f'<span class="hn-points">▲ {r["points"]}</span> '
                f'<a href="{escape(href or "")}" target="_blank" rel="noopener">'
                f'{escape(r["title"] or "")}</a> '
                f'<span class="hn-meta">'
                f'<a href="{escape(r["hn_url"])}" target="_blank" rel="noopener">'
                f'{r["num_comments"]} HN comments</a> &middot; '
                f'{escape((r["created_at"] or "")[:10])}</span>'
                f'</li>'
            )
        parts.append(
            "<h3>Recent HN mentions</h3>"
            f"<ul class='hn-list'>{''.join(items)}</ul>"
        )
    parts.append('</section>')
    return "\n".join(parts)


def build_index(db_path: Path, docs_dir: Path, repo: str) -> Path:
    docs_dir.mkdir(parents=True, exist_ok=True)
    rel = releases_df(db_path)
    prs = prs_df(db_path)
    cm = commits_df(db_path)
    now = datetime.now(timezone.utc)

    latest_html = _render_latest_release(db_path, repo)
    capability_html = render_capability_matrix(db_path, repo)
    perf_claims_html = _render_perf_claims(db_path)
    timeseries_html = _render_timeseries(db_path, prs)
    topics_html = _render_topics(db_path)
    momentum_html = _render_topic_momentum(db_path)
    drift_html = _render_release_drift(db_path)
    social_html = _render_social(db_path)
    hotspots_html = _render_issue_hotspots(db_path)
    forks_html = _render_forks(db_path)
    issues_html = _render_open_issues(db_path)
    digest_html = _render_digest_pointer(docs_dir)
    activity_html = _render_activity(rel, prs, cm, now)

    repo_url = f"https://github.com/{repo}"
    body = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>vLLM Insights — capability &amp; release intelligence</title>
<meta name="description" content="Live derived view of vLLM supported models, quantization methods, attention backends, parallelism, spec-decode and hardware platforms. Sourced from upstream registry.py and a recursive git-tree scan — no curation.">
<link rel="alternate" type="application/atom+xml" title="vLLM Insights — releases &amp; weekly digests" href="feed.xml">
<style>{PAGE_CSS}</style>
</head><body>
<header>
  <h1>vLLM Insights</h1>
  <p class="lede">
    <a href="{repo_url}">{escape(repo)}</a> &middot; supported models, quantization,
    attention backends, parallelism, spec-decode, LoRA, hardware platforms.
  </p>
  <p class="audience">
    Updated {now:%Y-%m-%d %H:%M UTC} · <a href="feed.xml">Atom feed</a>
  </p>
  <nav style="margin-top:.6rem">
    <a href="features/">Feature index</a>
    <a href="weekly/">Weekly digest</a>
    <a href="feed.xml">Atom</a>
    <a href="{repo_url}">Upstream</a>
  </nav>
</header>
{latest_html}
{capability_html}
{perf_claims_html}
{timeseries_html}
{topics_html}
{momentum_html}
{drift_html}
{social_html}
{hotspots_html}
{forks_html}
{issues_html}
{digest_html}
{activity_html}
<footer>vllm-insights &middot; refreshed hourly from
<a href="{repo_url}">{escape(repo)}</a>.</footer>
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
