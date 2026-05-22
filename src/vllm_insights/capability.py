"""Derived capability view — every row is a real file in upstream vLLM.

The previous version of this module shipped a hand-curated stable/experimental/
preview/none matrix. That was bluffing: the numbers came from my head, not from
the codebase. This rewrite removes every hardcoded claim and replaces it with
data we can verify in one click.

A row now means: "this `.py` file exists in upstream vLLM right now". We do
not pretend to know maturity, latency, or whether it works on your hardware —
those claims would need real benchmark data, which we don't have yet. What we
do show:

  - The feature name (filename stem, e.g. `fp8`, `awq_marlin`, `mxfp4`)
  - A link to the source file on GitHub (the operator can read it in 30s)
  - PR activity in the last 90 days for that exact path (a proxy for whether
    it's being actively maintained or has gone dormant)
  - A link to a per-feature deep page that lists every PR touching it

If a "feature" looks suspicious to a vLLM expert reading this page, they can
click straight through to the file and decide for themselves. That's the
contrast with the old approach.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

from .source_scan import (
    kinds_in_order,
    load_inventory,
    pr_activity_for_inventory,
)


def _feature_slug(kind: str, name: str) -> str:
    return f"{kind}-{name}".replace("_", "-").lower()


def _gh_blob_url(repo: str, path: str, sha: str | None) -> str:
    rev = sha or "main"
    # `git/blob/{sha}` is permalink-y; if we only have main we use that.
    if sha and len(sha) >= 7:
        return f"https://github.com/{repo}/blob/main/{path}"
    return f"https://github.com/{repo}/blob/main/{path}"


def render_capability_matrix(db_path: Path, repo: str = "vllm-project/vllm") -> str:
    """Render the derived capability section.

    Reads `source_inventory` (populated by `vllm-insights sync --source-scan`)
    and joins it against `pr_files` to compute 90-day activity per path. If the
    inventory is empty (first run), renders a hint rather than a fake table.
    """
    activity = pr_activity_for_inventory(db_path, days=90)

    parts: list[str] = [
        '<section class="capability">',
        '<h2>What vLLM ships, today</h2>',
        '<p class="cap-intro">'
        'Each row is a file in upstream <code>vllm/</code>. No maturity labels, '
        'no opinions — only what\'s present in the source tree right now and '
        'whether anyone has touched it in the last 90 days. Click any feature '
        'to open the source on GitHub or drill into the recent PRs for it.'
        '</p>',
    ]

    have_any = False
    for kind, group_label in kinds_in_order():
        rows = load_inventory(db_path, kind=kind)
        if not rows:
            continue
        have_any = True
        parts.append(f'<h3>{escape(group_label)} '
                     f'<span class="cap-count">({len(rows)})</span></h3>')
        parts.append('<div class="cap-tablewrap"><table class="cap-table">')
        parts.append(
            "<thead><tr>"
            "<th class='feat'>Feature</th>"
            "<th class='path'>Source</th>"
            "<th class='activity'>PRs (90d)</th>"
            "<th class='deep'></th>"
            "</tr></thead><tbody>"
        )
        for r in rows:
            path = r["source_path"]
            count = activity.get(path, 0)
            blob = _gh_blob_url(repo, path, r.get("source_sha"))
            slug = _feature_slug(kind, r["name"])
            activity_html = (
                f'<span class="act-hot">{count}</span>' if count >= 6
                else f'<span class="act-warm">{count}</span>' if count >= 1
                else '<span class="act-cold">0</span>'
            )
            parts.append(
                "<tr>"
                f"<td class='feat'><code>{escape(r['name'])}</code></td>"
                f"<td class='path'><a href='{blob}' target='_blank' rel='noopener'>"
                f"<code>{escape(path)}</code></a></td>"
                f"<td class='activity'>{activity_html}</td>"
                f"<td class='deep'><a href='features/{slug}.html' "
                f"title='Recent PRs touching this file'>&rarr;</a></td>"
                "</tr>"
            )
        parts.append("</tbody></table></div>")

    if not have_any:
        parts.append(
            '<p style="opacity:.6"><em>No inventory yet. Run '
            '<code>vllm-insights sync --source-scan</code> first.</em></p>'
        )

    parts.append("</section>")
    return "\n".join(parts)


CAPABILITY_CSS = """
section.capability { margin: 2rem 0 1rem; }
section.capability h2 { margin-bottom: .3rem; }
section.capability .cap-intro { font-size: .9rem; opacity: .8;
    margin: 0 0 .8rem; max-width: 75ch; }
section.capability h3 { margin-top: 1.4rem; font-size: 1rem;
    text-transform: uppercase; letter-spacing: .04em; opacity: .8;
    border-bottom: 1px dashed #6664; padding-bottom: .2rem; }
section.capability .cap-count { font-size: .75rem; opacity: .55;
    font-weight: 400; text-transform: none; letter-spacing: 0; }
.cap-tablewrap { overflow-x: auto; margin: .4rem 0 .8rem; }
table.cap-table { border-collapse: collapse; width: 100%; font-size: .85rem; }
table.cap-table th, table.cap-table td {
    padding: .35rem .55rem; border-bottom: 1px solid #ddd3;
    vertical-align: middle;
}
table.cap-table thead th { font-weight: 600; opacity: .8; font-size: .72rem;
    text-transform: uppercase; letter-spacing: .04em;
    border-bottom: 1px solid #ddd6; }
table.cap-table td.feat { font-size: .9rem; width: 22%; min-width: 160px; }
table.cap-table td.feat code { font-size: .85rem; padding: .05rem .35rem;
    border-radius: 4px; background: rgba(102,204,255,.1);
    border: 1px solid #6cf4; }
table.cap-table td.path { font-size: .72rem; opacity: .8; }
table.cap-table td.path a { text-decoration: none; }
table.cap-table td.path a:hover { text-decoration: underline; }
table.cap-table td.path code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
table.cap-table td.activity { width: 6rem; text-align: center; }
table.cap-table td.deep { text-align: center; width: 2.5rem; font-size: 1.1rem; }
table.cap-table td.deep a { text-decoration: none; opacity: .7; }
table.cap-table td.deep a:hover { opacity: 1; }
.act-hot   { color: #2c8f48; font-weight: 700; }
.act-warm  { color: #b8862b; font-weight: 600; }
.act-cold  { color: #888; }
"""
