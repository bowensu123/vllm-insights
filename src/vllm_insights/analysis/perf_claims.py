"""Extract author-claimed perf deltas from PR titles + bodies.

vLLM's real benchmark numbers live on perf.vllm.ai (Hex.tech app, no public
API) and hud.pytorch.org (Vercel bot-protected). We can't scrape either
reliably from a GitHub Actions worker.

What we CAN do honestly: PR authors regularly assert perf deltas in their
own words — "1.5x throughput on H100", "+12% TPS", "200 tok/s on Llama-70B".
Those claims are not measurements, but they're verifiable in one click
(open the PR, read the author's benchmark table). Surfacing them is honest
because we attribute every claim to its source PR.

We extract three claim shapes:

  - multiplier      "1.5x", "2.3× faster"
  - percent         "+12%", "20% improvement"
  - tokens_per_sec  "200 tok/s", "1.2k tps", "3210 tokens/s"

…and tag each with the hardware + model keywords mentioned nearby. Stored
in the `perf_claims` table; rendered on the homepage as a feed of recent
claims with PR links.
"""
from __future__ import annotations

import re
from pathlib import Path

from rich.console import Console

from ..db import connect

console = Console()


# Claim patterns. Anchored on the number so we can extract `value` for sorting.
# Order matters: the more specific tps/tok-s pattern goes first so "200 tps" doesn't
# match the percent rule on "200%".
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("tokens_per_sec",
        re.compile(r"\b(\d+(?:\.\d+)?)\s*(?:k\s*)?(?:tok(?:en)?s?(?:[/\s_]+sec(?:ond)?|/s|ps)|tps|TPS)\b",
                   re.IGNORECASE)),
    ("multiplier",
        re.compile(r"\b(\d+(?:\.\d+)?)\s*[x×]\b\s*(?:faster|speedup|speed[- ]up|throughput|perf)?",
                   re.IGNORECASE)),
    ("percent",
        re.compile(r"([+-]?\d+(?:\.\d+)?)\s*%\s*(?:faster|speedup|improvement|throughput|perf|reduction)",
                   re.IGNORECASE)),
]


# Hardware mention regex. Matches the canonical short form; we normalise to the
# label we use elsewhere (e.g. 'MI300X' uppercase).
_HW_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("H100",      re.compile(r"\bH100\b", re.IGNORECASE)),
    ("H200",      re.compile(r"\bH200\b", re.IGNORECASE)),
    ("B200",      re.compile(r"\bB200\b", re.IGNORECASE)),
    ("MI300X",    re.compile(r"\bMI300[Xx]?\b", re.IGNORECASE)),
    ("MI250",     re.compile(r"\bMI250\b", re.IGNORECASE)),
    ("A100",      re.compile(r"\bA100\b", re.IGNORECASE)),
    ("TPU",       re.compile(r"\b(?:TPU(?:\s*v?\d)?)\b", re.IGNORECASE)),
    ("Trainium",  re.compile(r"\bTrainium\d?\b", re.IGNORECASE)),
    ("CPU",       re.compile(r"\b(?:cpu|xeon|epyc|neoverse|arm)\b", re.IGNORECASE)),
]


_MODEL_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("llama",    re.compile(r"\bllama\b", re.IGNORECASE)),
    ("qwen",     re.compile(r"\bqwen\d?\b", re.IGNORECASE)),
    ("deepseek", re.compile(r"\bdeepseek\b", re.IGNORECASE)),
    ("mistral",  re.compile(r"\bmistral\b", re.IGNORECASE)),
    ("mixtral",  re.compile(r"\bmixtral\b", re.IGNORECASE)),
    ("gemma",    re.compile(r"\bgemma\b", re.IGNORECASE)),
    ("phi",      re.compile(r"\bphi-?\d?\b", re.IGNORECASE)),
    ("glm",      re.compile(r"\b(?:chatglm|glm-?\d?)\b", re.IGNORECASE)),
    ("minimax",  re.compile(r"\bminimax\b", re.IGNORECASE)),
]


# Words that frequently surround false positives (e.g. "10% chance of OOM" is
# not a perf claim). We require the matched snippet to be within ~80 chars of
# one of these positive context words.
_CONTEXT_HINTS = (
    "perf", "performance", "speed", "throughput", "latenc", "ttft",
    "tps", "tok/s", "faster", "improve", "speedup", "regression",
)


def _has_perf_context(text: str, span: tuple[int, int], radius: int = 80) -> bool:
    lo = max(0, span[0] - radius)
    hi = min(len(text), span[1] + radius)
    window = text[lo:hi].lower()
    return any(h in window for h in _CONTEXT_HINTS)


def _tag_first(text: str, patterns: list[tuple[str, re.Pattern[str]]],
               span: tuple[int, int], radius: int = 120) -> str | None:
    """Return the first tag whose pattern matches the text window around span."""
    lo = max(0, span[0] - radius)
    hi = min(len(text), span[1] + radius)
    window = text[lo:hi]
    for label, pat in patterns:
        if pat.search(window):
            return label
    return None


def _parse_value(kind: str, snippet: str) -> float | None:
    """Normalise the matched substring into a float for sorting."""
    m = re.search(r"([+-]?\d+(?:\.\d+)?)", snippet)
    if not m:
        return None
    val = float(m.group(1))
    # "1.2k tps" — only treat 'k' as a multiplier when it follows the digit and
    # is NOT just the letter 'k' inside "tok" / "token" / etc.
    if kind == "tokens_per_sec" and re.search(r"\d+(?:\.\d+)?\s*k\b", snippet, re.IGNORECASE):
        val *= 1000
    return val


def extract_claims(title: str, body: str) -> list[dict]:
    """Return one dict per claim found in `title` + `body`."""
    text = (title or "") + "\n" + (body or "")
    if not text.strip():
        return []
    out: list[dict] = []
    seen: set[tuple[str, int, int]] = set()
    for kind, pat in _PATTERNS:
        for m in pat.finditer(text):
            key = (kind, m.start(), m.end())
            if key in seen:
                continue
            seen.add(key)
            if not _has_perf_context(text, (m.start(), m.end())):
                continue
            snippet = text[m.start():m.end()].strip()
            out.append({
                "snippet": snippet[:80],
                "kind": kind,
                "value": _parse_value(kind, snippet),
                "hardware": _tag_first(text, _HW_PATTERNS, (m.start(), m.end())),
                "model_hint": _tag_first(text, _MODEL_PATTERNS, (m.start(), m.end())),
            })
    return out


def sync_perf_claims(db_path: Path) -> int:
    """Walk every PR with a non-empty title or body, extract claims, upsert."""
    n = 0
    with connect(db_path) as conn:
        conn.execute("DELETE FROM perf_claims")
        rows = conn.execute(
            "SELECT number, title, body FROM pull_requests "
            "WHERE merged_at IS NOT NULL"
        ).fetchall()
        for r in rows:
            for c in extract_claims(r["title"] or "", r["body"] or ""):
                conn.execute(
                    """INSERT OR IGNORE INTO perf_claims
                       (pr_number, snippet, kind, value, hardware, model_hint)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (r["number"], c["snippet"], c["kind"],
                     c["value"], c["hardware"], c["model_hint"]),
                )
                n += 1
    console.print(f"[cyan]Perf claims:[/] {n} from {len(rows)} PR(s)")
    return n


def recent_claims(db_path: Path, *, limit: int = 20) -> list[dict]:
    """Most recent claims, joined with their PR's merge date + url + title."""
    with connect(db_path) as conn:
        rows = conn.execute(
            """SELECT pc.*, p.title AS pr_title, p.url AS pr_url,
                      p.merged_at AS merged_at
               FROM perf_claims pc
               JOIN pull_requests p ON p.number = pc.pr_number
               WHERE p.merged_at IS NOT NULL
               ORDER BY p.merged_at DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]
