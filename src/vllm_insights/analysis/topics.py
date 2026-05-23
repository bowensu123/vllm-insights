"""Discover topics in PRs / issues by clustering their embeddings.

Pipeline
--------
1. Load L2-normalised embedding vectors from the `embeddings` table.
2. Run K-means (cosine similarity via dot product on unit-norm vectors)
   using numpy for speed — ~100× faster than the old pure-Python loop.
   We run `_RESTARTS` independent inits and keep the best by mean intra-
   cluster distance so a bad seed can't permanently corrupt the clusters.
3. K is chosen automatically via an elbow heuristic: we probe a short grid
   of candidate K values and stop adding clusters once 80 % of the total
   distance improvement has been captured.
4. For each cluster, ask an LLM for a 2-4-word topic label.  If the new
   cluster overlaps ≥ 60 % (Jaccard) with a cluster from the previous run,
   reuse the old label so topics don't drift every cron.
5. Persist assignments, labels, centroids, and mean intra-cluster distance.
   Storing centroids means `cluster_momentum` can assign newly-merged PRs
   (not yet re-clustered) to their nearest cluster on the fly.
6. `cluster_momentum` works for both PRs (filtered by merged_at) and issues
   (filtered by created_at) so both kinds can show trend direction.
"""
from __future__ import annotations

import json
import math
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from ..db import connect
from ..summarize import _call_anthropic, _call_github_models
from .embeddings import load_vectors


_RESTARTS = 3   # independent K-means inits per chosen K; best by intra-dist wins
_ELBOW_RESTARTS = 2   # cheaper restarts used during the K grid search
_ELBOW_ITERS = 15     # fewer iterations for the K grid search


# ---------------------------------------------------------------------------
# K heuristic (fallback when grid search can't run)
# ---------------------------------------------------------------------------
def _suggest_k(n: int) -> int:
    return max(12, min(40, int(math.sqrt(max(1, n) / 2))))


def _norm_rows(mat: np.ndarray) -> np.ndarray:
    """Row-wise L2 normalisation. Zero-norm rows are left unchanged."""
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms = np.where(norms < 1e-10, 1.0, norms)
    return mat / norms


# kept for single-vector callers outside this module
def _l2_normalise(vec: list[float]) -> list[float]:
    s = math.sqrt(sum(x * x for x in vec))
    return [x / s for x in vec] if s > 0 else vec


# ---------------------------------------------------------------------------
# K-means (cosine) — numpy implementation
# ---------------------------------------------------------------------------
def kmeans_cosine(
    vectors: list[list[float]],
    k: int,
    *,
    iters: int = 20,
    seed: int = 7,
) -> tuple[list[int], list[list[float]]]:
    """K-means with cosine similarity.

    Vectors are L2-normalised once so dot product == cosine similarity.
    Returns ``(assignments, centroids)`` as plain Python lists so callers
    don't need numpy.
    """
    if not vectors:
        return [], []

    rng = np.random.default_rng(seed)
    mat = _norm_rows(np.array(vectors, dtype=np.float32))
    n, d = mat.shape
    k = min(k, n)

    # k-means++ initialisation: each new centroid drawn proportional to
    # (1 - max_cosine_sim_to_existing_centroids) so we spread out.
    first = int(rng.integers(n))
    centroid_idx = [first]
    for _ in range(1, k):
        C = mat[centroid_idx]
        best_sim = (mat @ C.T).max(axis=1)
        dists = np.clip(1.0 - best_sim, 0.0, None)
        total = float(dists.sum())
        if total <= 0.0:
            centroid_idx.append(int(rng.integers(n)))
        else:
            centroid_idx.append(int(rng.choice(n, p=dists / total)))

    centroids = mat[centroid_idx].copy()
    assignments = np.zeros(n, dtype=np.int32)

    for _ in range(iters):
        new_asgn = (mat @ centroids.T).argmax(axis=1).astype(np.int32)
        changed = int((new_asgn != assignments).sum())
        assignments = new_asgn

        new_c = np.zeros_like(centroids)
        for c in range(k):
            members = mat[assignments == c]
            if len(members) == 0:
                new_c[c] = mat[int(rng.integers(n))]
            else:
                mean = members.mean(axis=0)
                norm = float(np.linalg.norm(mean))
                new_c[c] = mean / norm if norm > 1e-10 else mean
        centroids = new_c

        if changed < max(1, n // 200):
            break

    return assignments.tolist(), centroids.tolist()


# ---------------------------------------------------------------------------
# Quality metric: mean intra-cluster cosine distance
# ---------------------------------------------------------------------------
def _mean_intra_distance(
    mat: np.ndarray,
    assignments: list[int],
    centroids: list[list[float]],
) -> float:
    """Mean cosine distance from each vector to its assigned centroid.

    Lower = tighter clusters = better quality.  mat must already be
    L2-normalised (as produced by kmeans_cosine).
    """
    ctrs = np.array(centroids, dtype=np.float32)
    asgn = np.array(assignments, dtype=np.int32)
    sims = (mat * ctrs[asgn]).sum(axis=1)
    return float((1.0 - sims).mean())


# ---------------------------------------------------------------------------
# Multi-restart wrapper: run K times, keep best by intra-cluster distance
# ---------------------------------------------------------------------------
def _kmeans_best_of_n(
    vectors: list[list[float]],
    k: int,
    *,
    restarts: int = _RESTARTS,
    iters: int = 20,
) -> tuple[list[int], list[list[float]], float]:
    """Run K-means `restarts` times; return (assignments, centroids, mean_dist)
    for the run with the lowest mean intra-cluster cosine distance."""
    mat = _norm_rows(np.array(vectors, dtype=np.float32))
    best_asgn: list[int] | None = None
    best_ctrs: list[list[float]] | None = None
    best_dist = float("inf")
    for i in range(restarts):
        seed = i * 17 + 7    # spread seeds so runs are independent
        asgn, ctrs = kmeans_cosine(vectors, k, iters=iters, seed=seed)
        if not asgn:
            continue
        d = _mean_intra_distance(mat, asgn, ctrs)
        if d < best_dist:
            best_asgn, best_ctrs, best_dist = asgn, ctrs, d
    return best_asgn or [], best_ctrs or [], best_dist


# ---------------------------------------------------------------------------
# Automatic K selection via elbow (80 % variance-explained threshold)
# ---------------------------------------------------------------------------
def _auto_k_elbow(
    vectors: list[list[float]],
    *,
    restarts: int = _ELBOW_RESTARTS,
    iters: int = _ELBOW_ITERS,
) -> int:
    """Choose K by finding where adding more clusters stops helping.

    Probes a short grid of K values and returns the K that first accounts for
    ≥ 80 % of the total distance improvement from min_K to max_K.  Falls back
    to the heuristic `_suggest_k` if the grid is too small or degenerate.
    """
    n = len(vectors)
    lo = max(8, int(math.sqrt(max(1, n) / 4)))
    hi = min(45, max(lo + 5, int(math.sqrt(max(1, n)))))
    num_steps = 7
    step = max(1, (hi - lo) // (num_steps - 1))
    ks = sorted(set(range(lo, hi + 1, step)))
    if len(ks) < 2:
        return _suggest_k(n)

    print(f"  auto-K elbow: probing K={ks} on {n} vectors …")
    dists = [
        _kmeans_best_of_n(vectors, k, restarts=restarts, iters=iters)[2]
        for k in ks
    ]

    total = dists[0] - dists[-1]
    if total < 1e-4:
        print(f"  auto-K: trivial improvement curve; using K={ks[0]}")
        return ks[0]

    cumulative = 0.0
    for i in range(len(ks) - 1):
        cumulative += dists[i] - dists[i + 1]
        if cumulative / total >= 0.80:
            chosen = ks[i + 1]
            print(f"  auto-K elbow: chose K={chosen} (captured "
                  f"{cumulative / total:.0%} of improvement at step {i+1})")
            return chosen

    print(f"  auto-K elbow: no clear elbow; using K={ks[-1]}")
    return ks[-1]


# ---------------------------------------------------------------------------
# Representatives: top-N members closest to centroid
# ---------------------------------------------------------------------------
def _representative_members(
    assignments: list[int],
    centroids: list[list[float]],
    vectors: list[list[float]],
    ids: list[int],
    *,
    top: int = 8,
) -> dict[int, list[tuple[int, float]]]:
    mat = _norm_rows(np.array(vectors, dtype=np.float32))
    ctrs = _norm_rows(np.array(centroids, dtype=np.float32))
    sims = mat @ ctrs.T
    asgn = np.array(assignments)

    out: dict[int, list[tuple[int, float]]] = {}
    for c in range(len(centroids)):
        mask = np.where(asgn == c)[0]
        if len(mask) == 0:
            out[c] = []
            continue
        scored = sorted(
            ((ids[i], float(sims[i, c])) for i in mask),
            key=lambda t: -t[1],
        )
        out[c] = scored[:top]
    return out


# ---------------------------------------------------------------------------
# Label stability: reuse old labels when cluster membership overlaps enough
# ---------------------------------------------------------------------------
def _reuse_stable_labels(
    new_assignments: list[int],
    new_ids: list[int],
    prev_run_id: str,
    db_path: Path,
    kind: str,
    *,
    overlap_threshold: float = 0.6,
) -> dict[int, str]:
    """Return ``{new_cluster_id: old_label}`` for clusters whose Jaccard
    overlap with the best-matching cluster from *prev_run_id* is ≥ threshold.
    Clusters below the threshold get a fresh LLM label.
    """
    if not prev_run_id:
        return {}
    with connect(db_path) as conn:
        old_asgn = conn.execute(
            "SELECT entity_id, cluster FROM cluster_assignments "
            "WHERE run_id = ? AND kind = ?",
            (prev_run_id, kind),
        ).fetchall()
        old_labels = {
            r["cluster"]: r["label"]
            for r in conn.execute(
                "SELECT cluster, label FROM cluster_summary "
                "WHERE run_id = ? AND kind = ?",
                (prev_run_id, kind),
            ).fetchall()
        }

    old_members: dict[int, set[int]] = {}
    for r in old_asgn:
        old_members.setdefault(r["cluster"], set()).add(r["entity_id"])

    new_members: dict[int, set[int]] = {}
    for eid, c in zip(new_ids, new_assignments):
        new_members.setdefault(c, set()).add(eid)

    reuse: dict[int, str] = {}
    for nc, nm in new_members.items():
        best_j, best_label = 0.0, None
        for oc, om in old_members.items():
            inter = len(nm & om)
            union = len(nm | om)
            j = inter / union if union > 0 else 0.0
            if j > best_j:
                best_j, best_label = j, old_labels.get(oc)
        if best_j >= overlap_threshold and best_label:
            reuse[nc] = best_label
    return reuse


# ---------------------------------------------------------------------------
# LLM labelling
# ---------------------------------------------------------------------------
def _label_cluster(samples: list[str], kind: str, backend: str, model: str) -> str:
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


# ---------------------------------------------------------------------------
# Main clustering entry point
# ---------------------------------------------------------------------------
def run_clustering(
    db_path: Path,
    kind: str,
    *,
    k: int | None = None,
    backend: str | None = None,
    label_model: str | None = None,
    label_samples: int = 6,
) -> str:
    """Cluster embedded *kind* ('pr' | 'issue'), persist assignments + labels.

    Returns the run_id, or '' if there isn't enough data.
    """
    ids, vecs = load_vectors(db_path, kind)
    if len(ids) < 20:
        print(f"Not enough {kind} embeddings to cluster ({len(ids)}); skipping")
        return ""

    # Choose K: explicit override → elbow auto-select → heuristic fallback
    if k:
        K = k
        print(f"  K={K} (explicit override)")
    else:
        try:
            K = _auto_k_elbow(vecs)
        except Exception as e:  # noqa: BLE001
            K = _suggest_k(len(ids))
            print(f"  auto-K failed ({e}); falling back to heuristic K={K}")

    assignments, centroids, mean_dist = _kmeans_best_of_n(vecs, K, restarts=_RESTARTS)
    print(f"  K={K}, mean intra-cluster distance={mean_dist:.4f} "
          f"(best of {_RESTARTS} restarts)")

    reps = _representative_members(assignments, centroids, vecs, ids,
                                   top=max(label_samples, 8))
    title_lookup: dict[int, str] = {}
    with connect(db_path) as conn:
        tbl = "pull_requests" if kind == "pr" else "issues"
        for r in conn.execute(f"SELECT number, title FROM {tbl}").fetchall():
            title_lookup[r["number"]] = r["title"] or ""

    backend = backend or ("github" if os.getenv("GITHUB_TOKEN") else "anthropic")
    label_model = label_model or (
        "openai/gpt-4o-mini" if backend == "github" else "claude-haiku-4-5"
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    run_id = f"{kind}-{now_iso[:19].replace(':', '').replace('-', '')}"

    # Check previous run for label reuse
    prev_run_id = latest_cluster_run(db_path, kind) or ""
    reuse = _reuse_stable_labels(assignments, ids, prev_run_id, db_path, kind)
    reused_n = sum(1 for c in range(K) if c in reuse)
    if reused_n:
        print(f"  Reusing {reused_n}/{K} stable labels from previous run")

    cluster_sizes = [0] * K
    for a in assignments:
        cluster_sizes[a] += 1

    # Bulk cosine distances using normalised vectors + centroids
    mat = _norm_rows(np.array(vecs, dtype=np.float32))
    ctrs = np.array(centroids, dtype=np.float32)
    asgn_arr = np.array(assignments, dtype=np.int32)
    sims = (mat * ctrs[asgn_arr]).sum(axis=1)
    distances = (1.0 - sims).tolist()

    with connect(db_path) as conn:
        for i, entity_id in enumerate(ids):
            conn.execute(
                "INSERT INTO cluster_assignments"
                "(run_id, kind, entity_id, cluster, distance) VALUES(?,?,?,?,?)",
                (run_id, kind, entity_id, assignments[i], distances[i]),
            )

        for c in range(K):
            samples_ids = [eid for eid, _ in reps[c][:label_samples]]
            samples = [s for s in (title_lookup.get(eid, "") for eid in samples_ids)
                       if s.strip()]
            if not samples:
                label = "empty"
            elif c in reuse:
                label = reuse[c]
            else:
                label = _label_cluster(samples, kind, backend, label_model)
            conn.execute(
                "INSERT INTO cluster_summary"
                "(run_id, kind, cluster, label, size, sample_ids, "
                " centroid_json, mean_distance, created_at)"
                " VALUES(?,?,?,?,?,?,?,?,?)",
                (run_id, kind, c, label, cluster_sizes[c],
                 json.dumps(samples_ids), json.dumps(centroids[c]),
                 mean_dist, now_iso),
            )
    return run_id


# ---------------------------------------------------------------------------
# Nearest-centroid assignment for entities not yet in cluster_assignments
# ---------------------------------------------------------------------------
def _assign_unindexed(
    db_path: Path,
    kind: str,
    run_id: str,
    from_iso: str,
    to_iso: str | None,
) -> dict[int, int]:
    """Return ``{cluster: count}`` for entities in [from_iso, to_iso) that
    have embeddings but no assignment in *run_id* — assigned to nearest centroid.

    For kind='pr' filters on merged_at; for kind='issue' filters on created_at.
    Used by cluster_momentum to keep counts current without a full re-cluster.
    """
    if kind == "pr":
        tbl = "pull_requests"
        time_col = "merged_at"
        null_check = "AND p.merged_at IS NOT NULL"
    else:
        tbl = "issues"
        time_col = "created_at"
        null_check = ""

    with connect(db_path) as conn:
        c_rows = conn.execute(
            "SELECT cluster, centroid_json FROM cluster_summary "
            "WHERE run_id = ? AND kind = ? AND centroid_json IS NOT NULL",
            (run_id, kind),
        ).fetchall()
        if not c_rows:
            return {}
        cluster_ids = [r["cluster"] for r in c_rows]
        centroids = np.array(
            [json.loads(r["centroid_json"]) for r in c_rows], dtype=np.float32
        )
        centroids = _norm_rows(centroids)

        date_filter = f"AND p.{time_col} < ?" if to_iso else ""
        params = (kind, from_iso) + ((to_iso,) if to_iso else ()) + (run_id,)
        rows = conn.execute(
            f"""SELECT e.entity_id, e.vec
                FROM embeddings e
                JOIN {tbl} p ON p.number = e.entity_id
                WHERE e.kind = ?
                  {null_check}
                  AND p.{time_col} >= ?
                  {date_filter}
                  AND NOT EXISTS (
                    SELECT 1 FROM cluster_assignments ca
                    WHERE ca.run_id = ? AND ca.kind = e.kind
                      AND ca.entity_id = e.entity_id
                  )""",
            params,
        ).fetchall()

    if not rows:
        return {}

    vecs = np.array(
        [json.loads(r["vec"])["v"] for r in rows], dtype=np.float32
    )
    vecs = _norm_rows(vecs)
    best_c_idx = (vecs @ centroids.T).argmax(axis=1)

    counts: dict[int, int] = {}
    for idx in best_c_idx.tolist():
        c = cluster_ids[idx]
        counts[c] = counts.get(c, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------
def latest_cluster_run(db_path: Path, kind: str) -> str | None:
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT run_id FROM cluster_summary WHERE kind = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (kind,),
        ).fetchone()
    return row["run_id"] if row else None


# ---------------------------------------------------------------------------
# Momentum: current window vs prior window, including post-cluster entities
# ---------------------------------------------------------------------------
def cluster_momentum(
    db_path: Path,
    kind: str = "pr",
    *,
    window_days: int = 30,
) -> list[dict]:
    """For each cluster, compare entity counts in the last *window_days* vs the
    prior *window_days*.  Entities created/merged after the clustering run are
    assigned to their nearest centroid on the fly.

    For kind='pr': compares PRs by merged_at.
    For kind='issue': compares issues by created_at.

    Returns rows sorted by growth ratio descending.
    """
    rid = latest_cluster_run(db_path, kind)
    if not rid:
        return []

    now = datetime.now(timezone.utc)
    cur_start = now - timedelta(days=window_days)
    prev_start = now - timedelta(days=window_days * 2)
    cur_start_iso = cur_start.isoformat()
    prev_start_iso = prev_start.isoformat()

    if kind == "pr":
        tbl = "pull_requests"
        time_col = "merged_at"
        null_check = "AND p.merged_at IS NOT NULL"
    else:
        tbl = "issues"
        time_col = "created_at"
        null_check = ""

    with connect(db_path) as conn:
        run_ts_row = conn.execute(
            "SELECT MIN(created_at) AS t FROM cluster_summary WHERE run_id = ? AND kind = ?",
            (rid, kind),
        ).fetchone()
        if run_ts_row and run_ts_row["t"]:
            try:
                run_age = (now - datetime.fromisoformat(run_ts_row["t"])).days
                if run_age > 7:
                    print(f"  cluster_momentum: latest {kind} run is {run_age}d old; "
                          "including unassigned via nearest-centroid")
            except Exception:  # noqa: BLE001
                pass

        cur_rows = conn.execute(
            f"""SELECT ca.cluster, COUNT(DISTINCT ca.entity_id) AS n
               FROM cluster_assignments ca
               JOIN {tbl} p ON p.number = ca.entity_id
               WHERE ca.run_id = ? AND ca.kind = ?
                 {null_check}
                 AND p.{time_col} >= ?
               GROUP BY ca.cluster""",
            (rid, kind, cur_start_iso),
        ).fetchall()
        prev_rows = conn.execute(
            f"""SELECT ca.cluster, COUNT(DISTINCT ca.entity_id) AS n
               FROM cluster_assignments ca
               JOIN {tbl} p ON p.number = ca.entity_id
               WHERE ca.run_id = ? AND ca.kind = ?
                 {null_check}
                 AND p.{time_col} >= ? AND p.{time_col} < ?
               GROUP BY ca.cluster""",
            (rid, kind, prev_start_iso, cur_start_iso),
        ).fetchall()
        labels = {
            r["cluster"]: r["label"]
            for r in conn.execute(
                "SELECT cluster, label FROM cluster_summary WHERE run_id = ? AND kind = ?",
                (rid, kind),
            ).fetchall()
        }

    cur_map: dict[int, int] = {r["cluster"]: r["n"] for r in cur_rows}
    prev_map: dict[int, int] = {r["cluster"]: r["n"] for r in prev_rows}

    # Add counts for entities after the clustering run (nearest-centroid assignment)
    new_cur = _assign_unindexed(db_path, kind, rid, cur_start_iso, None)
    new_prev = _assign_unindexed(db_path, kind, rid, prev_start_iso, cur_start_iso)
    for c, n in new_cur.items():
        cur_map[c] = cur_map.get(c, 0) + n
    for c, n in new_prev.items():
        prev_map[c] = prev_map.get(c, 0) + n

    out: list[dict] = []
    for cluster, label in labels.items():
        cur = cur_map.get(cluster, 0)
        prev = prev_map.get(cluster, 0)
        if cur + prev == 0:
            continue
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


# ---------------------------------------------------------------------------
# Per-PR cluster lookup (used by feature pages)
# ---------------------------------------------------------------------------
def cluster_for_pr(db_path: Path, pr_number: int) -> dict | None:
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


# ---------------------------------------------------------------------------
# Top clusters for the homepage
# ---------------------------------------------------------------------------
def load_top_clusters(db_path: Path, kind: str, *, top: int = 10) -> list[dict]:
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
