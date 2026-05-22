"""Mirror vLLM's model registry into our SQLite cache.

vLLM declares every supported architecture in
`vllm/model_executor/models/registry.py` as a handful of module-level dicts:

    _TEXT_GENERATION_MODELS    = {"LlamaForCausalLM": ("llama", "LlamaForCausalLM"), ...}
    _MULTIMODAL_MODELS         = {...}
    _EMBEDDING_MODELS          = {...}
    _SPECULATIVE_DECODING_MODELS = {...}
    _SEQUENCE_CLASSIFICATION_MODELS = {...}
    _TOKEN_CLASSIFICATION_MODELS    = {...}
    _REWARD_MODELS             = {...}
    _LATE_INTERACTION_MODELS   = {...}
    _TRANSCRIPTION_MODELS      = {...}

We fetch the raw file from GitHub, parse it with `ast` (safe — no code is
executed), and upsert every entry into the `model_registry` table. The grouping
dict name maps onto a coarse `category` column the dashboard renders from.

This module deliberately uses plain httpx (no GitHub auth) so it works even
when running on a fork without a PAT — the raw URL is public.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
from pathlib import Path

import httpx

from .db import connect, set_sync_state

RAW_URL = (
    "https://raw.githubusercontent.com/vllm-project/vllm/main/"
    "vllm/model_executor/models/registry.py"
)

# Map the dict name inside registry.py → our coarse category.
_DICT_TO_CATEGORY: dict[str, str] = {
    "_TEXT_GENERATION_MODELS": "text",
    "_MULTIMODAL_MODELS": "multimodal",
    "_EMBEDDING_MODELS": "embedding",
    "_SPECULATIVE_DECODING_MODELS": "speculative",
    "_SEQUENCE_CLASSIFICATION_MODELS": "classification",
    "_TOKEN_CLASSIFICATION_MODELS": "classification",
    "_REWARD_MODELS": "reward",
    "_LATE_INTERACTION_MODELS": "late_interaction",
    "_TRANSCRIPTION_MODELS": "transcription",
    "_CROSS_ENCODER_MODELS": "cross_encoder",
}


def fetch_registry_source(url: str = RAW_URL, timeout: float = 30.0) -> str:
    """Download the raw registry.py text."""
    with httpx.Client(timeout=timeout, follow_redirects=True) as c:
        r = c.get(url)
        r.raise_for_status()
        return r.text


def parse_registry_source(src: str) -> dict[str, list[tuple[str, str, str]]]:
    """Parse registry.py source.

    Returns: {category: [(arch_class, module_name, impl_class), ...]} keyed by
    our coarse category. Entries inside unknown dicts are silently skipped —
    new dicts in upstream registry.py simply require a one-line addition to
    `_DICT_TO_CATEGORY`.

    Robust to upstream stylistic shifts: tolerates string values that are bare
    strings (rare), trailing commas, nested calls etc. We only extract entries
    where both value-tuple elements are string constants; anything we can't
    safely read is skipped rather than guessed.
    """
    tree = ast.parse(src)
    out: dict[str, list[tuple[str, str, str]]] = {}

    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        category = _DICT_TO_CATEGORY.get(target.id)
        if category is None:
            continue
        if not isinstance(node.value, ast.Dict):
            continue

        bucket = out.setdefault(category, [])
        for key_node, val_node in zip(node.value.keys, node.value.values):
            if not isinstance(key_node, ast.Constant) or not isinstance(key_node.value, str):
                continue
            arch_class = key_node.value

            # Common case: a 2-tuple of string constants.
            module_name = ""
            impl_class = arch_class
            if isinstance(val_node, ast.Tuple) and len(val_node.elts) >= 2:
                first, second = val_node.elts[0], val_node.elts[1]
                if (
                    isinstance(first, ast.Constant)
                    and isinstance(first.value, str)
                    and isinstance(second, ast.Constant)
                    and isinstance(second.value, str)
                ):
                    module_name = first.value
                    impl_class = second.value
                else:
                    # Skip non-string-tuple values; safer than guessing
                    continue
            else:
                # Unknown value shape — skip
                continue
            bucket.append((arch_class, module_name, impl_class))
    return out


def sync_registry(db_path: Path, *, source: str | None = None) -> dict[str, int]:
    """Fetch + parse + upsert. Returns per-category counts seen this run.

    Pass `source` to inject a literal registry.py string (used by tests).
    """
    src = source if source is not None else fetch_registry_source()
    parsed = parse_registry_source(src)
    now_iso = datetime.now(timezone.utc).isoformat()

    counts: dict[str, int] = {}
    seen: set[str] = set()
    with connect(db_path) as conn:
        for category, entries in parsed.items():
            counts[category] = len(entries)
            for arch_class, module_name, impl_class in entries:
                seen.add(arch_class)
                conn.execute(
                    """INSERT INTO model_registry(
                           arch_class, category, module_name, impl_class,
                           first_seen_at, last_seen_at, removed_at)
                       VALUES(?, ?, ?, ?, ?, ?, NULL)
                       ON CONFLICT(arch_class) DO UPDATE SET
                           category    = excluded.category,
                           module_name = excluded.module_name,
                           impl_class  = excluded.impl_class,
                           last_seen_at = excluded.last_seen_at,
                           removed_at  = NULL""",
                    (arch_class, category, module_name, impl_class, now_iso, now_iso),
                )
        # Mark anything previously known but missing today as removed (don't delete —
        # we want to be able to surface "vendor X dropped arch Y in v0.Z").
        rows = conn.execute(
            "SELECT arch_class FROM model_registry WHERE removed_at IS NULL"
        ).fetchall()
        for r in rows:
            if r["arch_class"] not in seen:
                conn.execute(
                    "UPDATE model_registry SET removed_at = ? WHERE arch_class = ?",
                    (now_iso, r["arch_class"]),
                )
        set_sync_state(conn, "registry", now_iso)
    return counts


def load_registry(db_path: Path, *, include_removed: bool = False) -> list[dict]:
    """Return all current registry rows as dicts."""
    sql = "SELECT * FROM model_registry"
    if not include_removed:
        sql += " WHERE removed_at IS NULL"
    sql += " ORDER BY category, arch_class"
    with connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]
