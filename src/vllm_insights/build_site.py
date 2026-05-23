"""Build the static homepage + supporting pages under docs/ for GitHub Pages.

The page is composed of product-shaped sections (hero + collapsible
sections in a 2-column layout with a floating ToC) — see `ui.py` for the
shell primitives and design tokens. The data each section renders is
unchanged; this module only wires the data into the new chrome.
"""
import json
import os
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
from .analysis.social import hottest_recent_prs, recent_hn_mentions
from .analysis.topics import (
    cluster_for_pr, cluster_momentum, load_top_clusters,
)
from .analysis.benchmarks import load_recent_benchmarks
from .analyzer.queries import (
    releases_df, prs_df, commits_df, classify_pr_by_title, merge_time_stats,
)
from .capability import CAPABILITY_CSS, render_capability_matrix
from .db import connect
from .hero import build_upgrade_hero, build_status_strip, _backfill_progress
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
from .ui import (
    COMPONENTS_CSS,
    DESIGN_TOKENS_CSS,
    Section,
    badge,
    empty_state,
    progress_bar,
    section_shell,
)


PAGE_CSS = DESIGN_TOKENS_CSS + COMPONENTS_CSS + """
/* ----- Section-specific styles (tables, cards, charts) ----- */

/* Sub-panels (merged sections) */
.sub-panel { }
.sub-panel + .sub-panel { border-top: 1px solid var(--border-soft); margin-top: 2rem; padding-top: 1.75rem; }
.sub-panel-head {
    font-size: .72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .1em; color: var(--fg-3);
    margin: 0 0 1rem;
    padding-left: .65rem;
    border-left: 2px solid var(--accent);
}

/* Capability cards still use their own table styling */
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
         gap: .75rem; margin: 1rem 0; }
.card { padding: .75rem 1rem; border: 1px solid var(--border-soft); border-radius: var(--r-md);
        background: var(--bg-2); }
.card .v { font-size: 1.4rem; font-weight: 600; }
.card .l { font-size: .8rem; color: var(--fg-3); }
.chart { margin: 1rem 0; }

/* Release-verdict summary box */
.release-summary {
  border-left: 3px solid var(--accent);
  background: var(--accent-soft);
  padding: .25rem 1.1rem 1rem;
  margin: 1rem 0 1.5rem;
  border-radius: 0 var(--r-md) var(--r-md) 0;
}
.release-summary > summary { cursor: pointer; font-weight: 600;
    font-size: .82rem; text-transform: uppercase; letter-spacing: .05em;
    padding: .5rem 0; list-style: revert; color: var(--fg-2); }
.release-summary > summary:hover { color: var(--fg); }
.release-summary h3 { margin-top: 1rem; font-size: .98rem;
    text-transform: uppercase; letter-spacing: .04em;
    color: var(--fg); border-bottom: 1px dashed var(--border);
    padding-bottom: .25rem; }
.release-summary p { margin: .4rem 0; color: var(--fg); }
.release-summary ul { padding-left: 1.4rem; margin: .4rem 0; }
.release-summary li { margin: .25rem 0; color: var(--fg); }
.release-summary .meta { display: block; margin-top: 1rem;
    font-size: .72rem; color: var(--fg-3); }

/* Vendor cards (supported-models grid) */
.models-intro { font-size: .9rem; color: var(--fg-2); margin: .2rem 0 1rem; }
.vendor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
               gap: .9rem; margin: .6rem 0 1.4rem; }
.vendor-card { border: 1px solid var(--border-soft); border-radius: var(--r-md);
    padding: .85rem 1rem; background: var(--bg-2);
    display: flex; flex-direction: column; gap: .55rem; }
.vendor-card .vendor-head { display: flex; align-items: baseline; gap: .5rem;
    flex-wrap: wrap; }
.vendor-card .vendor-name { font-size: 1.02rem; font-weight: 600; }
.vendor-card .vendor-name a { color: var(--fg); }
.vendor-card .vendor-name a:hover { color: var(--accent); }
.vendor-card .tagline { font-size: .85rem; color: var(--fg-2); margin: 0; }
.vendor-card .row-label { font-size: .65rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: .08em;
    color: var(--fg-3); margin-right: .35rem; }
.vendor-card .row { font-size: .8rem; line-height: 1.7; }
.pill { display: inline-block; padding: .05rem .45rem; margin: 0 .2rem .2rem 0;
    border-radius: 10px; border: 1px solid var(--border); font-size: .72rem;
    background: var(--bg-3); white-space: nowrap; color: var(--fg-2); }
.pill.arch { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .68rem; border-color: var(--accent); color: var(--accent);
    background: var(--accent-soft); }
.pill.modal { text-transform: capitalize; border-color: var(--derived);
    color: var(--derived); background: var(--derived-bg); }
.pill.feat { border-color: var(--new); color: var(--new); background: var(--new-bg); }
.vendor-card .new-list { margin: .25rem 0 0; padding-left: 1.1rem; font-size: .82rem; }
.vendor-card .new-list li { margin: .15rem 0; }
.vendor-card .no-new { font-size: .78rem; color: var(--fg-3); font-style: italic; margin: 0; }
.vendor-card .pill.arch.removed {
    text-decoration: line-through; opacity: .55;
    border-color: var(--hot); color: var(--hot); background: var(--hot-bg);
}
.vendor-card .arch-list { display: flex; flex-direction: column; gap: .4rem; }
.vendor-card .arch-group { display: block; }
.vendor-card .arch-cat { font-size: .65rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: .06em; color: var(--fg-3);
    margin-right: .45rem; }
.vendor-card .arch-cat.removed-cat { color: var(--hot); opacity: .9; }
.vendor-card .vendor-activity { font-size: .78rem;
    border-top: 1px dashed var(--border); padding-top: .4rem; }
.vendor-card .vendor-activity .row-label { display: block; margin-bottom: .15rem; }
.vendor-card .registry-meta { font-size: .68rem; color: var(--fg-3);
    border-top: 1px dashed var(--border); padding-top: .35rem; margin-top: .2rem; }
.act-hot   { color: var(--new); font-weight: 700; }
.act-warm  { color: var(--watch); font-weight: 600; }
.act-cold  { color: var(--fg-3); }

/* Collapsible vendor card */
.vc-d { }
.vc-summary {
  cursor: pointer; list-style: none; user-select: none;
  display: flex; align-items: center; gap: .5rem; flex-wrap: nowrap;
  padding: .15rem 0; min-width: 0; }
.vc-summary::-webkit-details-marker { display: none; }
.vc-stats {
  display: flex; gap: .4rem; align-items: center; flex-wrap: wrap;
  font-size: var(--t-xs); color: var(--fg-3); margin-left: auto; flex-shrink: 1; min-width: 0; }
.vc-stat {
  white-space: nowrap; padding: .1rem .35rem; border-radius: 999px;
  border: 1px solid var(--border); background: var(--bg-3); }
.vc-new     { color: var(--new);  background: var(--new-bg);  border-color: var(--new); }
.vc-removed { color: var(--hot);  background: var(--hot-bg);  border-color: var(--hot); }
.vc-chevron { color: var(--fg-3); font-size: var(--t-sm); flex-shrink: 0;
  transition: transform 200ms; }
.vc-chevron::after { content: '▾'; }
details[open].vc-d > summary .vc-chevron { transform: rotate(180deg); }
.vc-body {
  padding-top: var(--s-2); border-top: 1px solid var(--border-soft);
  margin-top: .3rem; display: flex; flex-direction: column; gap: .55rem; }

/* Digest pointer block */
.digest-pointer { display: block; padding: .8rem 1rem; margin: 1rem 0 1.5rem;
    border: 1px solid var(--border-soft); border-radius: var(--r-md);
    background: var(--bg-2); text-decoration: none; color: inherit;
    transition: border-color 150ms ease; }
.digest-pointer:hover { border-color: var(--accent); background: var(--accent-soft); }
.digest-pointer h3 { margin: 0 0 .25rem; font-size: 1rem; color: var(--fg); }
.digest-pointer p { margin: 0; font-size: .85rem; color: var(--fg-2); }

/* Forks list */
ul.fork-list { list-style: none; padding: 0; }
ul.fork-list > li { padding: .55rem 0; border-bottom: 1px solid var(--border-soft); font-size: .9rem; }
ul.fork-list > li:last-child { border-bottom: 0; }
.fork-meta { font-size: .72rem; color: var(--fg-3); margin-left: .4rem; }
ul.fork-commits { margin: .35rem 0 .1rem 1rem; padding-left: .8rem;
    border-left: 2px solid var(--accent); font-size: .78rem; }
ul.fork-commits li { padding: .15rem 0; color: var(--fg-2); }
.fork-c-meta { color: var(--fg-3); font-size: .68rem; }

/* Topic grid */
.topic-grid { display: flex; flex-wrap: wrap; gap: .4rem; margin: .4rem 0 .8rem; }
.topic-pill { padding: .35rem .7rem; border-radius: 12px;
    border: 1px solid var(--accent); background: var(--accent-soft);
    display: flex; flex-direction: column; gap: .1rem; min-width: 110px; }
.topic-label { font-size: .82rem; font-weight: 600; color: var(--fg); }
.topic-size { font-size: .68rem; color: var(--fg-3); }

/* Issue hotspots */
ul.hotspot-list { list-style: none; padding: 0; }
ul.hotspot-list li { padding: .35rem 0; border-bottom: 1px solid var(--border-soft);
    font-size: .88rem; }
ul.hotspot-list a { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.hot-count { font-size: .7rem; color: var(--watch); margin-left: .4rem;
    padding: .02rem .35rem; border-radius: 4px; background: var(--watch-bg);
    border: 1px solid var(--watch); }

/* Drift table */
table.drift-table { border-collapse: collapse; width: 100%; font-size: .85rem;
    margin-top: .4rem; }
table.drift-table th, table.drift-table td {
    padding: .35rem .55rem; border-bottom: 1px solid var(--border-soft);
    text-align: left; vertical-align: middle; }
table.drift-table th { font-size: .68rem; text-transform: uppercase;
    letter-spacing: .04em; color: var(--fg-3); }
table.drift-table td.dir code { font-size: .78rem; }
table.drift-table td.files { width: 5rem; text-align: right; color: var(--fg-3); }
table.drift-table td.changes { font-size: .78rem; position: relative; }
.changes-bar { height: 3px; background: linear-gradient(90deg, var(--new) 0%, var(--watch) 100%);
    margin-top: .25rem; border-radius: 2px; }

/* Bench table */
table.bench-table { border-collapse: collapse; width: 100%; font-size: .82rem;
    margin-top: .4rem; }
table.bench-table th, table.bench-table td {
    padding: .3rem .5rem; border-bottom: 1px solid var(--border-soft); text-align: left;
    color: var(--fg); }
table.bench-table th { color: var(--fg-3); font-size: .68rem;
    text-transform: uppercase; letter-spacing: .04em; }
table.bench-table th.num, table.bench-table td.num { text-align: right;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
table.bench-table td.obs { font-size: .72rem; color: var(--fg-3);
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }

/* Perf claims */
ul.claims-list { list-style: none; padding: 0; }
ul.claims-list li { padding: .35rem 0; border-bottom: 1px solid var(--border-soft);
    font-size: .88rem; display: flex; flex-wrap: wrap; align-items: baseline; gap: .35rem; }
.claim-snip { font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: .82rem; color: var(--new); font-weight: 700; }
.claim-tag { padding: .02rem .35rem; border-radius: 4px; font-size: .68rem;
    border: 1px solid var(--border); color: var(--fg-2); }
.claim-tag.hw { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
.claim-tag.model { background: var(--derived-bg); border-color: var(--derived); color: var(--derived); }
.footnote { font-size: .72rem; color: var(--fg-3); margin: .6rem 0 0; }

/* Momentum grid */
.momentum-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
@media (max-width: 700px) { .momentum-grid { grid-template-columns: 1fr; } }
.momentum-col h3 { font-size: .82rem; margin: .3rem 0 .4rem;
    text-transform: uppercase; letter-spacing: .04em; color: var(--fg-3); }
.momentum-col ul { list-style: none; padding: 0; margin: 0; }
.momentum-col li { display: flex; justify-content: space-between;
    padding: .3rem 0; border-bottom: 1px solid var(--border-soft); font-size: .85rem; }
.momentum-col .topic-label { font-weight: 500; }
.momentum-col .momentum.up   { color: var(--new); font-size: .8rem; font-family: ui-monospace, Menlo, monospace; }
.momentum-col .momentum.down { color: var(--watch); font-size: .8rem; font-family: ui-monospace, Menlo, monospace; }
.momentum-col .momentum .ratio { color: var(--fg); font-weight: 600; margin-left: .3rem; }

/* Social */
ul.hot-prs, ul.hn-list { list-style: none; padding: 0; }
ul.hot-prs li, ul.hn-list li { padding: .35rem 0;
    border-bottom: 1px solid var(--border-soft); font-size: .85rem;
    display: flex; flex-wrap: wrap; align-items: baseline; gap: .4rem; }
.react-total { font-weight: 700; font-size: .85rem; min-width: 2rem; color: var(--watch); }
.react-em { font-size: .78rem; color: var(--fg-2); font-family: -apple-system, sans-serif; }
.hn-points { font-weight: 700; color: #ff6600; min-width: 3rem; font-size: .85rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.hn-meta { font-size: .72rem; color: var(--fg-3); margin-left: .35rem; }

/* Issue label chips */
.issue-label { display: inline-block; font-size: .65rem;
    padding: .02rem .35rem; margin-left: .2rem; border-radius: 6px;
    border: 1px solid var(--border); background: var(--bg-3); color: var(--fg-2); }
.issue-meta { font-size: .7rem; color: var(--fg-3); margin-left: .4rem; }

/* Mobile: hide horizontal-scrolling tables in favour of stacked cards */
@media (max-width: 760px) {
  .cap-table thead { display: none; }
  .cap-table tbody, .cap-table tr, .cap-table td { display: block; width: 100%; }
  .cap-table tr { border: 1px solid var(--border-soft); border-radius: var(--r-md);
    padding: .5rem .7rem; margin-bottom: .5rem; background: var(--bg-2); }
  .cap-table td { border: 0; padding: .2rem 0; }
  .cap-table td.feat { font-size: .9rem; }
  .cap-table td.path { font-size: .7rem; word-break: break-all; }
}
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
            f'{total} architecture{"" if total == 1 else "s"}'
            + (f' &middot; {len(removed_archs)} dropped' if removed_archs else "")
            + '</div>'
        )

        # Summary stat chips shown at a glance in the collapsed header
        stat_chips: list[str] = [f'<span class="vc-stat">{total} arch{"s" if total != 1 else ""}</span>']
        if pr_count_90d:
            stat_chips.append(
                f'<span class="vc-stat {activity_class}">'
                f'{pr_count_90d} PR{"s" if pr_count_90d != 1 else ""} / 90d</span>'
            )
        if items:
            stat_chips.append(
                f'<span class="vc-stat vc-new">{len(items)} new</span>'
            )
        if removed_archs:
            stat_chips.append(
                f'<span class="vc-stat vc-removed">{len(removed_archs)} dropped</span>'
            )
        stats_html = "".join(stat_chips)

        body_parts: list[str] = []
        if cat_pills:
            body_parts.append(
                f'<div class="row"><span class="row-label">Categories</span>{cat_pills}</div>'
            )
        if arch_blocks:
            body_parts.append('<div class="arch-list">' + "".join(arch_blocks) + '</div>')
        body_parts.append(activity_html)
        body_parts.append(new_block)
        body_parts.append(registry_meta)

        cards.append(
            '<div class="vendor-card">'
            '<details class="vc-d">'
            '<summary class="vc-summary">'
            f'<span class="vendor-name">{head}</span>'
            f'<span class="vc-stats">{stats_html}</span>'
            '<span class="vc-chevron" aria-hidden="true"></span>'
            '</summary>'
            f'<div class="vc-body">{"".join(body_parts)}</div>'
            '</details>'
            '</div>'
        )

    return '<div class="vendor-grid">' + "\n".join(cards) + "</div>"


def _latest_release_payload(db_path: Path) -> dict | None:
    """Single helper used by both the release + supported-models sections."""
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT tag, name, published_at, url FROM releases "
            "WHERE is_prerelease = 0 ORDER BY published_at DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        latest = dict(row)
        sections = conn.execute(
            "SELECT section, item FROM release_sections WHERE tag = ?",
            (latest["tag"],),
        ).fetchall()
        summary_row = conn.execute(
            "SELECT summary, model, backend FROM release_summaries WHERE tag = ?",
            (latest["tag"],),
        ).fetchone()
    latest["sections"] = [dict(s) for s in sections]
    latest["summary_row"] = dict(summary_row) if summary_row else None
    return latest


def _strip_md_sections(text: str, *headings: str) -> str:
    """Remove named ### sections from markdown.

    *headings* are lowercased prefix substrings matched against the heading text
    (e.g. "verdict" removes "### Verdict", "who should" removes "### Who should upgrade").
    """
    out: list[str] = []
    skip = False
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("###"):
            h = s[3:].strip().lower()
            skip = any(h.startswith(kw) for kw in headings)
        if not skip:
            out.append(ln)
    # drop trailing blank lines
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out)


def _render_latest_release(
    db_path: Path, repo: str, *, hero_shows_verdict: bool = False
) -> tuple[str, str]:
    """Render the release-verdict section body. Returns (body_html, tag).

    When *hero_shows_verdict* is True the hero already shows the verdict
    one-liner and the "Who should upgrade" bullets, so we strip those two
    sections from the LLM summary to avoid repeating the same content.
    """
    import markdown as md
    payload = _latest_release_payload(db_path)
    if not payload:
        return "", ""

    tag = payload["tag"]
    rel_url = payload["url"] or f"https://github.com/{repo}/releases/tag/{tag}"
    name = payload.get("name") or tag
    published = payload["published_at"][:10] if payload.get("published_at") else "?"

    summary_html = ""
    if payload["summary_row"]:
        summary_md = payload["summary_row"]["summary"] or ""
        if hero_shows_verdict:
            # Verdict headline + "Who should upgrade" are already in the hero.
            summary_md = _strip_md_sections(
                summary_md, "verdict", "who should"
            )
            label = "Breaking changes &amp; what's faster"
            open_attr = ""           # start collapsed — hero handles the lead
        else:
            label = "Upgrade verdict"
            open_attr = " open"

        rendered = md.markdown(summary_md, extensions=["tables", "fenced_code"])
        if rendered.strip():
            summary_html = (
                f"<details{open_attr} class='release-summary'>"
                f"<summary>{label}</summary>"
                f"{rendered}"
                "</details>"
            )

    body = f"""
<p>
  <a href="{escape(rel_url)}" target="_blank" rel="noopener"><strong>{escape(tag)}</strong></a>
  {escape("— " + name) if name and name != tag else ""}
  <span style="color:var(--fg-3)">&middot; published {escape(published)}</span>
</p>
{summary_html}
"""
    return body, tag


def _render_supported_models(db_path: Path, repo: str) -> str:
    """Render the supported-models vendor grid only."""
    payload = _latest_release_payload(db_path)
    by_focus: dict[str, list[tuple[str, str]]] = {}
    if payload:
        for s in payload["sections"]:
            if not looks_like_model_section(s["section"]):
                continue
            cls = classify_model(s["item"])
            if not cls:
                continue
            vendor, org = cls
            if is_focus_vendor(vendor):
                by_focus.setdefault(vendor, []).append((s["item"], org))
    return _render_focus_grid(by_focus, db_path, repo)


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

    return f'<ul class="issue-list">{"".join(items)}</ul>'


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
        or '<p><em>Not loaded yet.</em></p>'

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
    return f'<ul class="fork-list">{"".join(items)}</ul>'


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
    return f'{pr_html}{issue_html}'


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
    return f'<ul class="hotspot-list">{"".join(items)}</ul>'


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
        f'<p class="drift-pair"><code>{escape(from_tag)}</code> &rarr; '
        f'<code>{escape(to_tag)}</code></p>'
        "<table class='drift-table'>"
        "<thead><tr><th>Directory</th><th>Files</th><th>Lines changed</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
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
        "<table class='bench-table'>"
        "<thead><tr><th>Workload</th><th>Hardware</th><th>Metric</th>"
        "<th class='num'>Value</th><th>Observed</th></tr></thead>"
        f"<tbody>{body}</tbody></table>"
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
    return "\n".join(f'<div class="chart">{c}</div>' for c in charts)


def _render_topic_momentum(db_path: Path) -> str:
    """Top growing / shrinking clusters this month vs last."""
    rows = cluster_momentum(db_path, "pr", window_days=30)
    if not rows:
        return ""
    growing = [r for r in rows if r["ratio"] > 1.0 and r["current"] >= 1][:6]
    shrinking = list(reversed(
        [r for r in rows if r["ratio"] < 1.0 and r["previous"] >= 1]
    ))[:6]

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

    if not growing and not shrinking:
        # No directional signal: show most-active topics by recent count as fallback
        active = sorted(rows, key=lambda r: r["current"] + r["previous"], reverse=True)[:6]
        lis = "".join(
            f'<li><span class="topic-label">{escape(r["label"])}</span>'
            f'<span class="momentum" style="color:var(--fg-3);font-size:.8rem">'
            f'{r["current"]} / {r["previous"]}</span></li>'
            for r in active
        )
        return (
            '<p style="font-size:.78rem;color:var(--fg-3);margin:.2rem 0 .5rem">'
            'Activity roughly stable — showing most active topics.</p>'
            f'<div class="momentum-grid"><div class="momentum-col">'
            f'<h3>Most active (30d / prior 30d)</h3><ul>{lis}</ul></div></div>'
        )

    return (
        '<div class="momentum-grid">'
        + _block("Heating up", growing, "up")
        + _block("Cooling down", shrinking, "down")
        + '</div>'
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
        f'<ul class="claims-list">{"".join(items)}</ul>'
        '<p class="footnote">Self-reported deltas. Click through to verify. '
        'Canonical perf data: <a href="https://perf.vllm.ai/" target="_blank" '
        'rel="noopener">perf.vllm.ai</a>.</p>'
    )


def _render_social(db_path: Path) -> str:
    """PR reactions + HN aggregation."""
    hot = hottest_recent_prs(db_path, days=30, limit=8)
    hn = recent_hn_mentions(db_path, limit=8)
    if not hot and not hn:
        return ""
    parts = []
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

    return "\n".join(parts)


def _compute_section_signals(db_path: Path, prs: pd.DataFrame) -> dict:
    """Pre-compute the small bits of data we use to decide section badges
    and one-line summaries. Keeping it in one place avoids re-querying."""
    with connect(db_path) as conn:
        # Activity heat: PRs merged in last 7d
        recent_pr_n = conn.execute(
            "SELECT COUNT(*) AS n FROM pull_requests "
            "WHERE merged_at IS NOT NULL AND merged_at >= datetime('now','-7 days')"
        ).fetchone()["n"]
        # Open issues matching the same label set shown in _render_open_issues
        watch_n = conn.execute(
            "SELECT COUNT(*) AS n FROM issues WHERE state='OPEN' AND ("
            "  labels LIKE '%release-blocker%' OR "
            "  labels LIKE '%regression%' OR "
            "  labels LIKE '%performance%' OR "
            "  labels LIKE '%rfc%' OR "
            "  labels LIKE '%hardware%' OR "
            "  labels LIKE '%rocm%' OR "
            "  labels LIKE '%tpu%' OR "
            "  labels LIKE '%cpu%' OR "
            "  labels LIKE '%correctness%')"
        ).fetchone()["n"]
        # Most-reacted PR last 7d
        top_react = conn.execute(
            "SELECT MAX(COALESCE(reactions_total,0)) AS n FROM pull_requests "
            "WHERE merged_at >= datetime('now','-7 days')"
        ).fetchone()["n"] or 0
        # Latest release published date
        latest = conn.execute(
            "SELECT tag, published_at FROM releases "
            "WHERE is_prerelease=0 ORDER BY published_at DESC LIMIT 1"
        ).fetchone()
        # Perf claim count last 30d
        perf_claim_n = conn.execute(
            "SELECT COUNT(*) AS n FROM perf_claims pc "
            "JOIN pull_requests p ON p.number = pc.pr_number "
            "WHERE p.merged_at >= datetime('now','-30 days')"
        ).fetchone()["n"]
        # Cluster momentum top growth
        from .analysis.topics import cluster_momentum as _cm
        momentum = _cm(db_path, "pr", window_days=30)
        top_ratio = momentum[0]["ratio"] if momentum else 1.0
        top_growing = momentum[0]["label"] if momentum and momentum[0]["ratio"] > 1.5 else None
        # Latest fork ahead count
        fork_ahead_max = conn.execute(
            "SELECT MAX(ahead_by) AS n FROM forks"
        ).fetchone()["n"] or 0
        # Recent HN
        hn_n = conn.execute(
            "SELECT COUNT(*) AS n FROM hn_mentions "
            "WHERE created_at >= datetime('now','-30 days')"
        ).fetchone()["n"]

    is_new_release = False
    rel_age_days: int | None = None
    if latest and latest["published_at"]:
        try:
            d = datetime.fromisoformat(latest["published_at"].replace("Z", "+00:00"))
            rel_age_days = (datetime.now(timezone.utc) - d).days
            is_new_release = rel_age_days <= 14
        except Exception:  # noqa: BLE001
            pass

    return {
        "recent_pr_n": recent_pr_n,
        "watch_n": watch_n,
        "top_react": top_react,
        "is_new_release": is_new_release,
        "rel_age_days": rel_age_days,
        "perf_claim_n": perf_claim_n,
        "top_ratio": top_ratio,
        "top_growing": top_growing,
        "fork_ahead_max": fork_ahead_max,
        "hn_n": hn_n,
    }


def _sub_panel(title: str, body: str) -> str:
    """Wrap a renderer's output in a titled sub-panel block."""
    body = body.strip()
    if not body:
        return ""
    return (
        f'<div class="sub-panel">'
        f'<h3 class="sub-panel-head">{escape(title)}</h3>'
        f'{body}'
        f'</div>'
    )


def _make_sections(db_path: Path, docs_dir: Path, prs: pd.DataFrame,
                   rel: pd.DataFrame, cm: pd.DataFrame,
                   now: datetime, repo: str, signals: dict
                   ) -> list[tuple[Section, str]]:
    """Produce the ordered list of (Section, body_html) pairs — 7 sections.

    Section map (13 renderers → 7 sections):
      1. Latest release
      2. What changed  = perf claims + release drift
      3. Capability    = what vLLM ships (feature matrix)
      4. Models        = supported vendor / arch grid
      5. Trends        = time series + discovered topics + topic momentum
      6. Community     = social buzz + issue hotspots + open issues
      7. Deep dive     = forks + activity stats (collapsed)
    """
    sections: list[tuple[Section, str]] = []

    # ── 1. Latest release ────────────────────────────────────────────────────
    hero_shows_verdict = (
        signals["is_new_release"] or
        (signals["rel_age_days"] is not None and signals["rel_age_days"] < 45)
    )
    rel_body, rel_tag = _render_latest_release(
        db_path, repo, hero_shows_verdict=hero_shows_verdict
    )
    if rel_body:
        sections.append((Section(
            slug="latest-release",
            title="Latest release" + (f" — {rel_tag}" if rel_tag else ""),
            icon="🚀",
            badge_kind="new" if signals["is_new_release"] else "neutral",
            badge_label="just shipped" if signals["is_new_release"]
                        else (f'{signals["rel_age_days"]}d old'
                              if signals["rel_age_days"] is not None else ""),
            summary="Full release notes, changelog, and upgrade verdict.",
            default_open=not hero_shows_verdict,
            empty_state=empty_state("No release cached yet", "No release data yet."),
        ), rel_body))

    # ── 2. What changed ──────────────────────────────────────────────────────
    pc_kind = "hot" if signals["perf_claim_n"] >= 3 else "neutral"
    changed_body = (
        _sub_panel("Performance claims (30d)", _render_perf_claims(db_path)) +
        _sub_panel("Code movement between releases", _render_release_drift(db_path))
    )
    sections.append((Section(
        slug="what-changed",
        title="What changed",
        icon="⚡",
        badge_kind=pc_kind,
        badge_label=(f'{signals["perf_claim_n"]} perf claims'
                     if signals["perf_claim_n"] else "—"),
        summary="Author-reported speedups and which parts of the codebase moved.",
        empty_state=empty_state("Nothing yet", "Will fill in once data is loaded."),
    ), changed_body))

    # ── 3. Capability ────────────────────────────────────────────────────────
    sections.append((Section(
        slug="capability",
        title="What vLLM ships",
        icon="🛠️",
        badge_kind="neutral",
        badge_label="",
        summary="Quantization, attention, parallelism, spec-decode, LoRA, and hardware platforms.",
        empty_state=empty_state("Not loaded yet", "Will fill in once data is loaded."),
    ), render_capability_matrix(db_path, repo)))

    # ── 4. Supported models ──────────────────────────────────────────────────
    sections.append((Section(
        slug="supported-models",
        title="Supported models",
        icon="🧬",
        badge_kind="neutral",
        badge_label="",
        summary="Focus vendors and the architectures vLLM ships for each.",
        empty_state=empty_state("Not loaded yet", "Will fill in once data is loaded."),
    ), _render_supported_models(db_path, repo)))

    # ── 5. Trends & Topics ───────────────────────────────────────────────────
    mo_kind = "hot" if signals["top_ratio"] >= 2.0 else "neutral"
    trends_body = (
        _sub_panel("Growth over time", _render_timeseries(db_path, prs)) +
        _sub_panel("Discovered topics", _render_topics(db_path)) +
        _sub_panel("Topic momentum", _render_topic_momentum(db_path))
    )
    sections.append((Section(
        slug="trends",
        title="Trends & Topics",
        icon="📈",
        badge_kind=mo_kind,
        badge_label=(f'{signals["top_growing"]} trending'
                     if signals["top_growing"] else "stable"),
        summary="Activity trends, auto-discovered PR/issue themes, and what's heating up.",
        empty_state=empty_state(
            "Still building",
            progress_bar("Embedding progress", *_backfill_progress(db_path)) +
            "<p class='footnote' style='margin-top:.5rem'>Fills in once embeddings complete.</p>",
        ),
    ), trends_body))

    # ── 6. Community ─────────────────────────────────────────────────────────
    soc_kind = ("hot" if signals["top_react"] >= 10 or signals["hn_n"] >= 3
                else "watch" if signals["watch_n"] >= 1
                else "neutral")
    soc_label = (f'★{signals["top_react"]} reactions'
                 if signals["top_react"] >= 5
                 else f'{signals["watch_n"]} open issues'
                 if signals["watch_n"] else "—")
    community_body = (
        _sub_panel("Buzz & reactions", _render_social(db_path)) +
        _sub_panel("Issue hotspots", _render_issue_hotspots(db_path)) +
        _sub_panel("Open issues worth watching", _render_open_issues(db_path))
    )
    sections.append((Section(
        slug="community",
        title="Community",
        icon="🔥",
        badge_kind=soc_kind,
        badge_label=soc_label,
        summary="Most-reacted PRs, Hacker News mentions, and open issues to watch.",
        empty_state=empty_state("Nothing yet", "Will fill in once data is loaded."),
    ), community_body))

    # ── 7. Deep dive (collapsed) ─────────────────────────────────────────────
    fk_label = (f'top fork +{signals["fork_ahead_max"]} commits'
                if signals["fork_ahead_max"] else "—")
    deep_body = (
        _sub_panel("Active forks", _render_forks(db_path)) +
        _sub_panel("Repo activity stats", _render_activity(rel, prs, cm, now))
    )
    sections.append((Section(
        slug="deep-dive",
        title="Deep dive",
        icon="📊",
        badge_kind="hot" if signals["fork_ahead_max"] >= 50 else "neutral",
        badge_label=fk_label,
        summary="Diverged forks, commit cadence, and contributor stats.",
        default_open=False,
        empty_state=empty_state("Nothing yet", "Will fill in once data is loaded."),
    ), deep_body))

    return sections


def _render_topbar(repo_url: str) -> str:
    """Sticky top header with brand, nav, search box and theme toggle."""
    return f"""
<div class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="./" aria-label="vLLM Insights home">
      <span class="brand-mark">▮</span> vLLM Insights
    </a>
    <button class="topnav-toggle" type="button" aria-label="Toggle navigation"
            aria-expanded="false">☰</button>
    <nav class="topnav" aria-label="Sections">
      <a href="#latest-release">Release</a>
      <a href="#what-changed">Changed</a>
      <a href="#capability">Capability</a>
      <a href="#trends">Trends</a>
      <a href="#community">Community</a>
      <a href="features/">Features</a>
      <a href="weekly/">Weekly</a>
      <a href="about.html">About</a>
    </nav>
    <span class="topbar-spacer"></span>
    <div class="search-wrap">
      <input type="search" class="search-input" placeholder="Search PRs, features, vendors…"
             aria-label="Search" autocomplete="off">
      <div class="search-results" role="listbox"></div>
    </div>
    <a class="tool-btn" href="feed.xml" title="Atom feed" aria-label="Atom feed">RSS</a>
    <a class="tool-btn" href="{repo_url}" title="Upstream repo on GitHub"
       aria-label="vLLM on GitHub">GH</a>
    <button class="tool-btn" id="theme-toggle" type="button" aria-label="Toggle theme">◐</button>
  </div>
</div>
"""


def _render_toc(sections: list[tuple[Section, str]]) -> str:
    """Floating left-side ToC for desktop. Hidden on mobile."""
    items = "".join(
        f'<li><a href="#{escape(s.slug)}" data-slug="{escape(s.slug)}">'
        f'{escape(s.title)}</a></li>'
        for s, _ in sections
    )
    return f'<aside class="toc"><h3>On this page</h3><ul>{items}</ul></aside>'


def _render_hero(db_path: Path, repo_url: str) -> str:
    """Hero block — upgrade verdict (when available) or daily takeaway."""
    return build_upgrade_hero(
        db_path,
        repo_url,
        newsletter_username=os.getenv("BUTTONDOWN_USERNAME", ""),
    )


def _site_js() -> str:
    """Inline JS for: theme persistence, mobile-nav toggle, ToC active state,
    section collapse persistence, search."""
    return r"""
(() => {
  // ----- Theme toggle (persisted in localStorage) -----
  const root = document.documentElement;
  const stored = localStorage.getItem('vi-theme');
  if (stored === 'dark' || stored === 'light') root.setAttribute('data-theme', stored);
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const cur = root.getAttribute('data-theme') ||
        (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
      const next = cur === 'dark' ? 'light' : 'dark';
      root.setAttribute('data-theme', next);
      localStorage.setItem('vi-theme', next);
    });
  }

  // ----- Mobile nav toggle -----
  const navBtn = document.querySelector('.topnav-toggle');
  const nav = document.querySelector('.topnav');
  if (navBtn && nav) {
    navBtn.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      navBtn.setAttribute('aria-expanded', String(open));
    });
  }

  // ----- ToC active-section highlighting -----
  const tocLinks = Array.from(document.querySelectorAll('.toc a[data-slug]'));
  if ('IntersectionObserver' in window && tocLinks.length) {
    const map = new Map();
    tocLinks.forEach(a => map.set(a.dataset.slug, a));
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          tocLinks.forEach(a => a.classList.remove('active'));
          const a = map.get(e.target.id);
          if (a) a.classList.add('active');
        }
      });
    }, { rootMargin: '-30% 0px -55% 0px' });
    document.querySelectorAll('.sec[id]').forEach(s => io.observe(s));
  }

  // ----- Section open/close persistence -----
  document.querySelectorAll('.sec[id] .sec-d').forEach(d => {
    const slug = d.closest('.sec').id;
    const stored = localStorage.getItem('vi-sec-' + slug);
    if (stored === '0') d.removeAttribute('open');
    if (stored === '1') d.setAttribute('open', '');
    d.addEventListener('toggle', () => {
      localStorage.setItem('vi-sec-' + slug, d.open ? '1' : '0');
    });
  });

  // ----- Client-side search -----
  const input = document.querySelector('.search-input');
  const out = document.querySelector('.search-results');
  let idx = null, idxLoading = false;
  async function loadIdx() {
    if (idx || idxLoading) return idx;
    idxLoading = true;
    try {
      const r = await fetch('search-index.json');
      idx = await r.json();
    } catch {
      idx = { items: [] };
    } finally { idxLoading = false; }
    return idx;
  }
  function score(q, t) {
    const tq = q.toLowerCase(), tt = (t || '').toLowerCase();
    if (!tq) return 0;
    if (tt.startsWith(tq)) return 3;
    if (tt.includes(tq)) return 2;
    return 0;
  }
  if (input) {
    let debounceT = null;
    input.addEventListener('input', () => {
      clearTimeout(debounceT);
      debounceT = setTimeout(async () => {
        const q = input.value.trim();
        if (!q) { out.classList.remove('open'); out.innerHTML = ''; return; }
        await loadIdx();
        const hits = (idx.items || [])
          .map(it => ({ it, s: score(q, it.title) + score(q, it.kind) }))
          .filter(x => x.s > 0)
          .sort((a, b) => b.s - a.s)
          .slice(0, 25);
        if (!hits.length) {
          out.innerHTML = '<div class="sr-empty">No matches.</div>';
        } else {
          out.innerHTML = hits.map(({ it }) =>
            `<a href="${it.url}"><span class="sr-kind">${it.kind}</span>` +
            `<span class="sr-title">${it.title.replace(/</g, '&lt;')}</span></a>`
          ).join('');
        }
        out.classList.add('open');
      }, 120);
    });
    input.addEventListener('blur', () => setTimeout(() => out.classList.remove('open'), 200));
    input.addEventListener('focus', () => { if (out.innerHTML) out.classList.add('open'); });
  }
})();
"""


def _build_search_index(db_path: Path, docs_dir: Path) -> int:
    """Write docs/search-index.json — what the in-page search uses."""
    items: list[dict] = []
    with connect(db_path) as conn:
        for r in conn.execute(
            "SELECT tag, name, url FROM releases ORDER BY published_at DESC LIMIT 40"
        ).fetchall():
            items.append({"kind": "release",
                          "title": f"{r['tag']}{' — ' + (r['name'] or '') if r['name'] else ''}",
                          "url": r['url'] or '#latest-release'})
        for r in conn.execute(
            "SELECT number, title, url FROM pull_requests "
            "WHERE merged_at IS NOT NULL ORDER BY merged_at DESC LIMIT 500"
        ).fetchall():
            items.append({"kind": "PR",
                          "title": f"#{r['number']} {r['title']}",
                          "url": r['url'] or '#'})
        for r in conn.execute(
            "SELECT number, title, url FROM issues "
            "WHERE state='OPEN' ORDER BY updated_at DESC LIMIT 200"
        ).fetchall():
            items.append({"kind": "issue",
                          "title": f"#{r['number']} {r['title']}",
                          "url": r['url'] or '#'})
        for r in conn.execute(
            "SELECT kind, name FROM source_inventory ORDER BY kind, name"
        ).fetchall():
            slug = f"{r['kind']}-{r['name']}".replace('_', '-').lower()
            items.append({"kind": r['kind'],
                          "title": r['name'],
                          "url": f"features/{slug}.html"})
        for r in conn.execute(
            "SELECT arch_class, category FROM model_registry WHERE removed_at IS NULL"
        ).fetchall():
            items.append({"kind": "arch",
                          "title": f"{r['arch_class']} ({r['category']})",
                          "url": "#supported-models"})
    payload = {"items": items, "generated_at": datetime.now(timezone.utc).isoformat()}
    out = docs_dir / "search-index.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    return len(items)


def build_index(db_path: Path, docs_dir: Path, repo: str) -> Path:
    docs_dir.mkdir(parents=True, exist_ok=True)
    rel = releases_df(db_path)
    prs = prs_df(db_path)
    cm = commits_df(db_path)
    now = datetime.now(timezone.utc)
    repo_url = f"https://github.com/{repo}"

    signals = _compute_section_signals(db_path, prs)
    sections = _make_sections(db_path, docs_dir, prs, rel, cm, now, repo, signals)

    # Filter sections to those with body or with an empty-state design
    rendered: list[str] = []
    visible_sections: list[tuple[Section, str]] = []
    for sec, body in sections:
        html = section_shell(sec, body)
        if not html:
            continue
        rendered.append(html)
        visible_sections.append((sec, body))

    digest_html = _render_digest_pointer(docs_dir)

    # Build the search index alongside the page
    _build_search_index(db_path, docs_dir)

    topbar = _render_topbar(repo_url)
    hero = _render_hero(db_path, repo_url)
    toc = _render_toc(visible_sections)

    # OpenGraph + Twitter card values
    og_title = "vLLM Insights"
    og_desc = ("A live view of what vLLM is shipping — supported models, "
               "capability surface, release verdicts, community signals.")
    og_url = "https://bowensu123.github.io/vllm-insights/"

    body = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>vLLM Insights — capability matrix, release verdicts, topic trends</title>
<meta name="description" content="{escape(og_desc)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(og_title)}">
<meta property="og:description" content="{escape(og_desc)}">
<meta property="og:url" content="{escape(og_url)}">
<meta property="og:site_name" content="vLLM Insights">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{escape(og_title)}">
<meta name="twitter:description" content="{escape(og_desc)}">
<link rel="alternate" type="application/atom+xml"
      title="vLLM Insights — releases & weekly digests" href="feed.xml">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='12' fill='%232f6feb'/><text x='32' y='44' text-anchor='middle' font-family='-apple-system,sans-serif' font-size='38' font-weight='700' fill='white'>v</text></svg>">
<style>{PAGE_CSS}</style>
</head><body>
{topbar}
<main class="page">
  {hero}
  <div class="layout">
    {toc}
    <div class="sections">
      {"".join(rendered)}
      {digest_html}
    </div>
  </div>
  <footer class="foot">
    <div>vllm-insights &middot; refreshed hourly &middot;
      tracking <a href="{repo_url}">{escape(repo)}</a></div>
    <div>
      <a href="about.html">About</a> &middot;
      <a href="feed.xml">Atom</a> &middot;
      <a href="features/">Feature index</a>
    </div>
  </footer>
</main>
<script>{_site_js()}</script>
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
