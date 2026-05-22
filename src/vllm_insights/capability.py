"""vLLM capability matrix — hardware × quantization × parallelism × features.

This is a curated, opinionated answer to the question "if I'm running vLLM
today, what actually works on what?". It's the centerpiece of the homepage:
a vLLM engineer should be able to glance at it and know within five seconds
whether the combination they're planning is `stable`, `experimental`,
`preview`, or `none`.

Maturity scale:
  stable        — green-lit; CI gates and prod users
  experimental  — merged but expect rough edges / perf cliffs
  preview       — landed via flag or partial backend coverage
  none          — explicitly not supported / removed

Edit this file when upstream lands a feature. The dashboard renders the
matrix as-is; there's no auto-discovery yet (a future iteration could mine
PR titles + RFC issues to flag rows whose `since` looks stale).

Keep rows tight. One row = one decision a user makes when configuring a
serving rig.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# Column order matters — it's the order the matrix renders left→right.
HARDWARE_COLS: list[str] = [
    "H100",      # Hopper, the reference path
    "B200",      # Blackwell datacenter
    "MI300X",    # AMD CDNA3
    "TPU v5/v6", # Google TPU
    "Trainium2", # AWS
    "CPU",       # Intel/AMD CPU backend
]


@dataclass
class CapRow:
    """One row in the capability matrix.

    `support` keys must be a subset of HARDWARE_COLS. Missing keys render as
    "none". `since` is the vLLM version that crossed into the dominant
    maturity tier (not necessarily first appearance). `refs` are PR / issue
    numbers that anchor the claim — we don't fabricate; leave empty if
    unsure.
    """
    feature: str
    note: str
    support: dict[str, str]
    since: str = ""
    refs: list[str] = field(default_factory=list)


# -----------------------------------------------------------------------------
# Quantization
# -----------------------------------------------------------------------------
QUANTIZATION: list[CapRow] = [
    CapRow(
        feature="FP8 (e4m3, per-tensor + block)",
        note="The default fast-path on Hopper/Blackwell; block-wise is the DeepSeek-V3 recipe.",
        support={"H100": "stable", "B200": "stable", "MI300X": "experimental",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
        since="v0.6.x",
    ),
    CapRow(
        feature="FP4 (NVFP4 / MXFP4)",
        note="Blackwell-only inner kernel; Hopper falls back to FP8 dequant.",
        support={"H100": "experimental", "B200": "stable", "MI300X": "none",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
        since="v0.8.x",
    ),
    CapRow(
        feature="AWQ (W4A16)",
        note="Battle-tested int4 weight-only path; works for almost every dense decoder.",
        support={"H100": "stable", "B200": "stable", "MI300X": "stable",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "experimental"},
    ),
    CapRow(
        feature="GPTQ (W4A16 / W8A16)",
        note="Comparable accuracy to AWQ; Marlin kernels give the best Hopper throughput.",
        support={"H100": "stable", "B200": "stable", "MI300X": "stable",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "experimental"},
    ),
    CapRow(
        feature="GGUF (Q4_K_M, etc.)",
        note="Llama.cpp-style quant; useful for small CPU/edge serving, slow on GPU.",
        support={"H100": "preview", "B200": "preview", "MI300X": "none",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "stable"},
    ),
    CapRow(
        feature="BitsAndBytes (NF4 / 8-bit)",
        note="One-line load-time quant; convenient for dev, not optimal for prod throughput.",
        support={"H100": "stable", "B200": "stable", "MI300X": "experimental",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
]


# -----------------------------------------------------------------------------
# Attention / Kernel
# -----------------------------------------------------------------------------
ATTENTION: list[CapRow] = [
    CapRow(
        feature="FlashAttention-3",
        note="Hopper TMA/WGMMA kernel; the default attn backend on H100/H200.",
        support={"H100": "stable", "B200": "experimental", "MI300X": "none",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
    CapRow(
        feature="FlashInfer",
        note="Alternative attn backend with paged prefix-cache + spec-decode hooks.",
        support={"H100": "stable", "B200": "experimental", "MI300X": "none",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
    CapRow(
        feature="MLA (Multi-head Latent Attention)",
        note="DeepSeek-V2/V3 attention — required for serving DeepSeek MoE economically.",
        support={"H100": "stable", "B200": "stable", "MI300X": "experimental",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
    CapRow(
        feature="Lightning / linear hybrid attention",
        note="MiniMax-Text-01 style; long-context (1M+) hybrid blocks.",
        support={"H100": "experimental", "B200": "experimental", "MI300X": "none",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
    CapRow(
        feature="Sliding-window + global hybrid",
        note="Gemma 2/3 attention shape; supported in the default backend.",
        support={"H100": "stable", "B200": "stable", "MI300X": "stable",
                 "TPU v5/v6": "experimental", "Trainium2": "none", "CPU": "experimental"},
    ),
]


# -----------------------------------------------------------------------------
# Parallelism / scheduling
# -----------------------------------------------------------------------------
PARALLELISM: list[CapRow] = [
    CapRow(
        feature="Tensor Parallel (TP)",
        note="The default sharding for >24B dense models; NCCL all-reduce on intra-node.",
        support={"H100": "stable", "B200": "stable", "MI300X": "stable",
                 "TPU v5/v6": "stable", "Trainium2": "experimental", "CPU": "experimental"},
    ),
    CapRow(
        feature="Pipeline Parallel (PP)",
        note="Cross-node sharding for models that don't fit on one node even at TP=8.",
        support={"H100": "stable", "B200": "stable", "MI300X": "experimental",
                 "TPU v5/v6": "experimental", "Trainium2": "none", "CPU": "none"},
    ),
    CapRow(
        feature="Expert Parallel (EP / DeepEP)",
        note="MoE expert sharding; DeepEP all-to-all is what makes DeepSeek-V3 affordable.",
        support={"H100": "stable", "B200": "stable", "MI300X": "experimental",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
    CapRow(
        feature="Sequence Parallel (SP)",
        note="Splits the sequence axis to reduce activation memory under TP.",
        support={"H100": "experimental", "B200": "experimental", "MI300X": "experimental",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
    CapRow(
        feature="Chunked Prefill",
        note="Mixes prefill and decode in the same batch; eliminates head-of-line blocking.",
        support={"H100": "stable", "B200": "stable", "MI300X": "stable",
                 "TPU v5/v6": "experimental", "Trainium2": "experimental", "CPU": "preview"},
    ),
    CapRow(
        feature="Prefix Caching",
        note="Reuses KV across requests that share a prompt prefix; huge win for agent workloads.",
        support={"H100": "stable", "B200": "stable", "MI300X": "stable",
                 "TPU v5/v6": "experimental", "Trainium2": "none", "CPU": "preview"},
    ),
    CapRow(
        feature="PD Disaggregation",
        note="Decouples prefill workers from decode workers via KV transfer (NIXL / Mooncake).",
        support={"H100": "experimental", "B200": "experimental", "MI300X": "preview",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
]


# -----------------------------------------------------------------------------
# Decoding strategies
# -----------------------------------------------------------------------------
DECODING: list[CapRow] = [
    CapRow(
        feature="Speculative Decoding (EAGLE / Medusa)",
        note="Draft-and-verify acceleration; EAGLE-2/3 are the production paths.",
        support={"H100": "stable", "B200": "stable", "MI300X": "experimental",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
    CapRow(
        feature="MTP (Multi-Token Prediction)",
        note="DeepSeek-V3 native draft head; cheaper than EAGLE when the model trained for it.",
        support={"H100": "stable", "B200": "stable", "MI300X": "experimental",
                 "TPU v5/v6": "none", "Trainium2": "none", "CPU": "none"},
    ),
    CapRow(
        feature="N-gram / lookup decoding",
        note="No draft model; cheap speedup for repetitive completions (code, JSON).",
        support={"H100": "stable", "B200": "stable", "MI300X": "stable",
                 "TPU v5/v6": "experimental", "Trainium2": "none", "CPU": "experimental"},
    ),
    CapRow(
        feature="Structured outputs (xgrammar / outlines)",
        note="Constrained decoding to a JSON schema or grammar; CFG check inside the kernel.",
        support={"H100": "stable", "B200": "stable", "MI300X": "stable",
                 "TPU v5/v6": "experimental", "Trainium2": "experimental", "CPU": "experimental"},
    ),
    CapRow(
        feature="LoRA (multi-adapter)",
        note="Hot-swap adapters per request; throughput cliff at high adapter count.",
        support={"H100": "stable", "B200": "stable", "MI300X": "stable",
                 "TPU v5/v6": "experimental", "Trainium2": "none", "CPU": "preview"},
    ),
]


CAPABILITY_GROUPS: list[tuple[str, list[CapRow]]] = [
    ("Quantization", QUANTIZATION),
    ("Attention & kernels", ATTENTION),
    ("Parallelism & scheduling", PARALLELISM),
    ("Decoding & adapters", DECODING),
]


# -----------------------------------------------------------------------------
# HTML rendering
# -----------------------------------------------------------------------------
_CELL_CLASS = {
    "stable":       "cap-stable",
    "experimental": "cap-exp",
    "preview":      "cap-preview",
    "none":         "cap-none",
    "":             "cap-none",
}
_CELL_LABEL = {
    "stable":       "stable",
    "experimental": "exp",
    "preview":      "preview",
    "none":         "—",
    "":             "—",
}


def render_capability_matrix() -> str:
    """Render the full HxQxPxF matrix as an HTML block."""
    from html import escape

    parts: list[str] = [
        '<section class="capability">',
        '<h2>vLLM capability matrix</h2>',
        '<p class="cap-intro">'
        'What actually works, where, today. <span class="legend">'
        '<span class="cap-pill cap-stable">stable</span>'
        '<span class="cap-pill cap-exp">experimental</span>'
        '<span class="cap-pill cap-preview">preview</span>'
        '<span class="cap-pill cap-none">none</span></span>'
        '</p>',
    ]

    for group_name, rows in CAPABILITY_GROUPS:
        parts.append(f'<h3>{escape(group_name)}</h3>')
        parts.append('<div class="cap-tablewrap"><table class="cap-table">')
        # header
        parts.append("<thead><tr><th class='feat'>Feature</th>")
        for col in HARDWARE_COLS:
            parts.append(f"<th>{escape(col)}</th>")
        parts.append("<th class='since'>Since</th></tr></thead><tbody>")

        for row in rows:
            parts.append("<tr>")
            parts.append(
                f"<td class='feat'><strong>{escape(row.feature)}</strong>"
                f"<div class='cap-note'>{escape(row.note)}</div></td>"
            )
            for col in HARDWARE_COLS:
                level = row.support.get(col, "none")
                cls = _CELL_CLASS.get(level, "cap-none")
                label = _CELL_LABEL.get(level, "—")
                parts.append(
                    f"<td class='{cls}' title='{escape(level or 'none')}'>{escape(label)}</td>"
                )
            since = escape(row.since) if row.since else ""
            parts.append(f"<td class='since'>{since}</td>")
            parts.append("</tr>")
        parts.append("</tbody></table></div>")

    parts.append("</section>")
    return "\n".join(parts)


CAPABILITY_CSS = """
section.capability { margin: 2rem 0 1rem; }
section.capability h2 { margin-bottom: .3rem; }
section.capability .cap-intro { font-size: .9rem; opacity: .8;
    margin: 0 0 .8rem; display: flex; flex-wrap: wrap; align-items: center; gap: .6rem; }
section.capability .legend { display: inline-flex; gap: .3rem; flex-wrap: wrap; }
section.capability h3 { margin-top: 1.4rem; font-size: 1rem;
    text-transform: uppercase; letter-spacing: .04em; opacity: .8;
    border-bottom: 1px dashed #6664; padding-bottom: .2rem; }
.cap-tablewrap { overflow-x: auto; margin: .4rem 0 .8rem; }
table.cap-table { border-collapse: collapse; width: 100%; font-size: .82rem; }
table.cap-table th, table.cap-table td {
    padding: .35rem .55rem; border-bottom: 1px solid #ddd3; text-align: center;
    white-space: nowrap;
}
table.cap-table th { font-weight: 600; opacity: .85; border-bottom: 1px solid #ddd6; }
table.cap-table th.feat, table.cap-table td.feat { text-align: left; white-space: normal;
    width: 30%; min-width: 220px; }
table.cap-table td.feat strong { display: block; font-size: .88rem; }
.cap-note { font-size: .73rem; opacity: .6; line-height: 1.35; margin-top: .15rem; }
.cap-table th.since, .cap-table td.since { font-size: .72rem; opacity: .7;
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.cap-stable   { background: rgba(60,180,90,.18);  color: #2c8f48; font-weight: 600; }
.cap-exp      { background: rgba(255,170,40,.18); color: #b8862b; font-weight: 600; }
.cap-preview  { background: rgba(120,140,255,.16); color: #5468d6; font-weight: 600; }
.cap-none     { background: rgba(127,127,127,.07); color: #888; }
.cap-pill { padding: .05rem .45rem; border-radius: 10px; font-size: .7rem;
    border: 1px solid #8884; display: inline-block; }
"""
