"""Discover topics in PRs / issues by clustering their embeddings.

The clustering algorithm is plain K-means in numpy. We deliberately don't
pull sklearn for this — K-means is 30 lines and the input shape (~15k
vectors × 256 dims) is small enough that vectorised numpy on cosine distance
runs in well under a second.

For each cluster we then ask the LLM to read a handful of representative
titles and write a 2-4-word topic label. That converts "cluster 7" into
"FP8 kernels & quant configs" — which is the actual deliverable.

Cluster assignments + labels land in `cluster_assignments` and
`cluster_summary`. The homepage reads only `cluster_summary` for the top
N labels.
"""
from __future__ import annotations

import json
import math
import os
import random
from datetime import datetime, timezone
from pathlib import Path

from ..db import connect
from ..summarize import _call_anthropic, _call_github_models
from .embeddings import load_vectors


# K-means hyperparameters. We pick K heuristically: roughly sqrt(N/2),
# clamped to [12, 40]. That gives reasonable granularity for the few-hundred
# to few-thousand vectors a typical vLLM-insights snapshot has.
def _suggest_k(n: int) -> int:
    return max(12, min(40, int(math.sqrt(max(1, n) / 2))))


def _l2_normalise(vec: list[float]) -> list[float]:
    s = math.sqrt(sum(x * x for x in vec))
    if s <= 0:
        return vec
    return [x / s for x in vec]


def kmeans_cosine(vectors: list[list[float]], k: int, *,
                  iters: int = 20, seed: int = 7) -> tuple[list[int], list[list[float]]]:
    """Plain k-means with cosine similarity (works because we L2-normalise).

    Returns `(assignments, centroids)`. No numpy dependency on purpose — the
    inputs are small and avoiding numpy keeps the codebase boring.
    """
    if not vectors:
        return [], []
    rng = random.Random(seed)
    n = len(vectors)
    d = len(vectors[0])
    # L2-normalise once so dot product == cosine similarity.
    vecs = [_l2_normalise(v) for v in vectors]
    # k-means++ style init: first centroid at random, subsequent ones biased
    # away from already-chosen centroids.
    centroid_idx = [rng.randrange(n)]
    for _ in range(1, k):
        # Distance to nearest existing centroid (1 - cosine since unit-norm).
        dists = []
        for i in range(n):
            best = 0.0
            for ci in centroid_idx:
                dot = sum(vecs[i][j] * vecs[ci][j] for j in range(d))
                if dot > best:
                    best = dot
            dists.append(max(0.0, 1.0 - best))
        total = sum(dists)
        if total <= 0:
            centroid_idx.append(rng.randrange(n))
            continue
        # Weighted pick proportional to dist
        target = rng.random() * total
        acc = 0.0
        for i, dist in enumerate(dists):
            acc += dist
            if acc >= target:
                centroid_idx.append(i)
                break
    centroids = [list(vecs[i]) for i in centroid_idx]

    assignments = [0] * n
    for _ in range(iters):
        changed = 0
        for i in range(n):
            best_c, best_sim = 0, -2.0
            v = vecs[i]
            for c, ctr in enumerate(centroids):
                sim = sum(v[j] * ctr[j] for j in range(d))
                if sim > best_sim:
                    best_sim, best_c = sim, c
            if assignments[i] != best_c:
                changed += 1
            assignments[i] = best_c
        # Recompute centroids as the L2-normalised mean of their members.
        sums = [[0.0] * d for _ in range(k)]
        counts = [0] * k
        for i in range(n):
            c = assignments[i]
            counts[c] += 1
            for j in range(d):
                sums[c][j] += vecs[i][j]
        for c in range(k):
            if counts[c] == 0:
                # Re-seed empty cluster from a random point. Keeps k stable.
                seed_i = rng.randrange(n)
                centroids[c] = list(vecs[seed_i])
                continue
            avg = [s / counts[c] for s in sums[c]]
            centroids[c] = _l2_normalise(avg)
        if changed < max(1, n // 200):
            break
    return assignments, centroids


def _representative_members(
    assignments: list[int], centroids: list[list[float]],
    vectors: list[list[float]], ids: list[int], *, top: int = 8,
) -> dict[int, list[tuple[int, float]]]:
    """For each cluster, return the `top` member ids closest to the centroid."""
    out: dict[int, list[tuple[int, float]]] = {}
    vecs = [_l2_normalise(v) for v in vectors]
    for c in range(len(centroids)):
        member_idx = [i for i, a in enumerate(assignments) if a == c]
        scored = []
        for i in member_idx:
            sim = sum(vecs[i][j] * centroids[c][j] for j in range(len(centroids[c])))
            scored.append((ids[i], sim))
        scored.sort(key=lambda t: -t[1])
        out[c] = scored[:top]
    return out


def _label_cluster(samples: list[str], kind: str,
                   backend: str, model: str) -> str:
    """Ask the LLM for a 2-4-word topic label from a handful of titles."""
    sys = (
        "You name clusters of vLLM "
        + ("pull request" if kind == "pr" else "GitHub issue")
        + " titles. Output one short topic label of 2-4 words, no quotes, "
        "no period. Focus on the concrete technical theme — kernels, attention, "
        "quantization, parallelism, hardware backend, model family, etc. "
        "If the cluster is incoherent, output 'misc'."
    )
    user = "Titles in this cluster:\n" + "\n".join(f"- {t}" for t in samples)
    try:
        if backend == "anthropic":
            return _call_anthropic(sys, user, model).strip().splitlines()[0][:60]
        return _call_github_models(sys, user, model).strip().splitlines()[0][:60]
    except Exception as e:  # noqa: BLE001
        return f"misc (label failed: {type(e).__name__})"


def run_clustering(
    db_path: Path,
    kind: str,
    *,
    k: int | None = None,
    backend: str | None = None,
    label_model: str | None = None,
    label_samples: int = 6,
) -> str:
    """Cluster the given `kind` ('pr' | 'issue'), write assignments + LLM
    cluster labels, return the run_id.

    No-op if there are fewer than 20 embedded entities (clustering needs
    enough data to be meaningful).
    """
    ids, vecs = load_vectors(db_path, kind)
    if len(ids) < 20:
        print(f"Not enough {kind} embeddings to cluster ({len(ids)}); skipping")
        return ""
    K = k or _suggest_k(len(ids))
    assignments, centroids = kmeans_cosine(vecs, K)

    # Gather representatives + their titles for LLM labelling.
    reps = _representative_members(assignments, centroids, vecs, ids,
                                   top=max(label_samples, 8))
    title_lookup: dict[int, str] = {}
    with connect(db_path) as conn:
        if kind == "pr":
            for r in conn.execute("SELECT number, title FROM pull_requests").fetchall():
                title_lookup[r["number"]] = r["title"] or ""
        else:
            for r in conn.execute("SELECT number, title FROM issues").fetchall():
                title_lookup[r["number"]] = r["title"] or ""

    # Pick a backend for labelling. GitHub Models is free for OSS repos.
    backend = backend or (
        "github" if os.getenv("GITHUB_TOKEN") else "anthropic"
    )
    if backend == "github":
        label_model = label_model or "openai/gpt-4o-mini"
    else:
        label_model = label_model or "claude-haiku-4-5"

    now_iso = datetime.now(timezone.utc).isoformat()
    run_id = f"{kind}-{now_iso[:19].replace(':', '').replace('-', '')}"

    cluster_sizes = [0] * K
    for a in assignments:
        cluster_sizes[a] += 1

    with connect(db_path) as conn:
        # Write assignments
        for i, entity_id in enumerate(ids):
            sim = sum(_l2_normalise(vecs[i])[j] * centroids[assignments[i]][j]
                      for j in range(len(centroids[0])))
            conn.execute(
                """INSERT INTO cluster_assignments(run_id, kind, entity_id, cluster, distance)
                   VALUES(?, ?, ?, ?, ?)""",
                (run_id, kind, entity_id, assignments[i], 1.0 - sim),
            )

        # For each cluster, get sample titles and ask LLM to label
        for c in range(K):
            samples_ids = [eid for eid, _ in reps[c][:label_samples]]
            samples = [title_lookup.get(eid, "") for eid in samples_ids]
            samples = [s for s in samples if s.strip()]
            if not samples:
                label = "empty"
            else:
                label = _label_cluster(samples, kind, backend, label_model)
            conn.execute(
                """INSERT INTO cluster_summary(run_id, kind, cluster, label,
                                                size, sample_ids, created_at)
                   VALUES(?, ?, ?, ?, ?, ?, ?)""",
                (run_id, kind, c, label, cluster_sizes[c],
                 json.dumps(samples_ids), now_iso),
            )
    return run_id


def latest_cluster_run(db_path: Path, kind: str) -> str | None:
    """Most recent run_id for a kind; None if no clustering has been done yet."""
    with connect(db_path) as conn:
        row = conn.execute(
            """SELECT run_id FROM cluster_summary WHERE kind = ?
               ORDER BY created_at DESC LIMIT 1""",
            (kind,),
        ).fetchone()
    return row["run_id"] if row else None


def cluster_momentum(db_path: Path, kind: str = "pr",
                     *, window_days: int = 30) -> list[dict]:
    """For each cluster in the latest run, compute PR counts in the last
    `window_days` vs the previous `window_days`. Returns rows sorted by
    growth ratio descending.

    A "story" emerges naturally: clusters where this-window > prior-window
    are heating up; the reverse is cooling. We don't editorialise — the
    numbers do the talking.
    """
    rid = latest_cluster_run(db_path, kind)
    if not rid:
        return []
    if kind != "pr":
        # Issue momentum exists but is less useful (issue activity is dominated
        # by comments, which we don't currently track); skip for now.
        return []

    with connect(db_path) as conn:
        # Active window count
        cur_rows = conn.execute(
            """SELECT ca.cluster, COUNT(DISTINCT ca.entity_id) AS n
               FROM cluster_assignments ca
               JOIN pull_requests p ON p.number = ca.entity_id
               WHERE ca.run_id = ? AND ca.kind = ?
                 AND p.merged_at IS NOT NULL
                 AND p.merged_at >= datetime('now', ?)
               GROUP BY ca.cluster""",
            (rid, kind, f"-{window_days} days"),
        ).fetchall()
        # Prior window count
        prev_rows = conn.execute(
            """SELECT ca.cluster, COUNT(DISTINCT ca.entity_id) AS n
               FROM cluster_assignments ca
               JOIN pull_requests p ON p.number = ca.entity_id
               WHERE ca.run_id = ? AND ca.kind = ?
                 AND p.merged_at IS NOT NULL
                 AND p.merged_at >= datetime('now', ?)
                 AND p.merged_at <  datetime('now', ?)
               GROUP BY ca.cluster""",
            (rid, kind,
             f"-{window_days * 2} days", f"-{window_days} days"),
        ).fetchall()
        labels = {
            r["cluster"]: r["label"]
            for r in conn.execute(
                "SELECT cluster, label FROM cluster_summary "
                "WHERE run_id = ? AND kind = ?",
                (rid, kind),
            ).fetchall()
        }

    cur_map = {r["cluster"]: r["n"] for r in cur_rows}
    prev_map = {r["cluster"]: r["n"] for r in prev_rows}
    out: list[dict] = []
    for cluster, label in labels.items():
        cur = cur_map.get(cluster, 0)
        prev = prev_map.get(cluster, 0)
        if cur + prev == 0:
            continue
        if cur == 0 and prev == 0:
            continue
        # Smoothed ratio so a 0→3 jump shows up properly without divide-by-zero.
        ratio = (cur + 1) / (prev + 1)
        out.append({
            "cluster": cluster,
            "label": label,
            "current": cur,
            "previous": prev,
            "ratio": ratio,
        })
    out.sort(key=lambda r: r["ratio"], reverse=True)
    return out


def cluster_for_pr(db_path: Path, pr_number: int) -> dict | None:
    """Get the cluster label for one PR (latest run). Used by other UI
    sections to badge PRs with their topic."""
    rid = latest_cluster_run(db_path, "pr")
    if not rid:
        return None
    with connect(db_path) as conn:
        row = conn.execute(
            """SELECT cs.cluster, cs.label
               FROM cluster_assignments ca
               JOIN cluster_summary cs
                 ON cs.run_id = ca.run_id AND cs.kind = ca.kind
                AND cs.cluster = ca.cluster
               WHERE ca.run_id = ? AND ca.kind = 'pr' AND ca.entity_id = ?""",
            (rid, pr_number),
        ).fetchone()
    return dict(row) if row else None


def load_top_clusters(db_path: Path, kind: str, *, top: int = 10) -> list[dict]:
    """Top `top` clusters from the most recent run, ordered by size desc.
    Returns rows with label, size, and sample_ids (parsed)."""
    rid = latest_cluster_run(db_path, kind)
    if not rid:
        return []
    with connect(db_path) as conn:
        rows = conn.execute(
            """SELECT cluster, label, size, sample_ids
               FROM cluster_summary
               WHERE run_id = ? AND kind = ?
                 AND lower(label) NOT IN ('misc', 'empty')
               ORDER BY size DESC LIMIT ?""",
            (rid, kind, top),
        ).fetchall()
    out = []
    for r in rows:
        try:
            samples = json.loads(r["sample_ids"]) if r["sample_ids"] else []
        except Exception:  # noqa: BLE001
            samples = []
        out.append({
            "cluster": r["cluster"],
            "label": r["label"],
            "size": r["size"],
            "sample_ids": samples,
        })
    return out
