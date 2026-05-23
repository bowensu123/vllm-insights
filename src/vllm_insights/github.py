"""Thin GitHub REST client. Uses REST (simpler than GraphQL) with pagination + rate-limit awareness."""
import time
from typing import Any, Iterator
import httpx

API = "https://api.github.com"


class GitHubClient:
    def __init__(self, token: str, repo: str):
        self.repo = repo
        self.client = httpx.Client(
            base_url=API,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "vllm-insights/0.1",
            },
            timeout=30.0,
        )

    def close(self) -> None:
        self.client.close()

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        for attempt in range(5):
            r = self.client.request(method, path, **kwargs)
            # Primary rate limit
            if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
                reset = int(r.headers.get("X-RateLimit-Reset", "0"))
                sleep_for = max(reset - int(time.time()), 1) + 1
                time.sleep(min(sleep_for, 900))
                continue
            # Secondary rate limit / abuse detection
            if r.status_code in (429, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            return r
        r.raise_for_status()
        return r

    def paginate(self, path: str, params: dict | None = None) -> Iterator[dict[str, Any]]:
        params = dict(params or {})
        params.setdefault("per_page", 100)
        url = path
        while url:
            r = self._request("GET", url, params=params if url == path else None)
            data = r.json()
            if isinstance(data, list):
                yield from data
            else:
                yield data
                return
            # Parse Link header for next URL
            link = r.headers.get("Link", "")
            next_url = None
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part[part.find("<") + 1 : part.find(">")]
                    # strip base
                    if next_url.startswith(API):
                        next_url = next_url[len(API):]
            url = next_url

    # --- entity endpoints ---

    def list_releases(self) -> Iterator[dict]:
        yield from self.paginate(f"/repos/{self.repo}/releases")

    def list_pulls(self, state: str = "all", since_iso: str | None = None) -> Iterator[dict]:
        # /pulls doesn't support since; sort desc by updated and stop early
        params = {"state": state, "sort": "updated", "direction": "desc"}
        for pr in self.paginate(f"/repos/{self.repo}/pulls", params=params):
            if since_iso and pr.get("updated_at") and pr["updated_at"] < since_iso:
                return
            yield pr

    def list_commits(self, since_iso: str | None = None) -> Iterator[dict]:
        params: dict[str, Any] = {}
        if since_iso:
            params["since"] = since_iso
        yield from self.paginate(f"/repos/{self.repo}/commits", params=params)

    def list_issues(self, since_iso: str | None = None, labels: str | None = None,
                    state: str = "all") -> Iterator[dict]:
        """List issues (NOT pull requests). The REST /issues endpoint returns both;
        we filter PRs out client-side by skipping anything with a 'pull_request' key.

        `labels` is a comma-separated string of label names (any-of semantics on GH).
        """
        params: dict[str, Any] = {"state": state, "sort": "updated", "direction": "desc"}
        if labels:
            params["labels"] = labels
        if since_iso:
            params["since"] = since_iso
        for it in self.paginate(f"/repos/{self.repo}/issues", params=params):
            if "pull_request" in it:
                continue
            yield it

    def get_tree(self, tree_sha: str = "main", recursive: bool = True) -> dict:
        """Fetch the full git tree at `tree_sha` (a branch or commit SHA).
        Returns the raw API response; the `tree` field is the list of entries.

        Note: GitHub truncates trees over ~100k entries (see `truncated` field).
        vLLM is well under that threshold today.
        """
        params = {"recursive": "1"} if recursive else None
        r = self._request("GET", f"/repos/{self.repo}/git/trees/{tree_sha}", params=params)
        return r.json()

    def get_last_commit_for_path(self, path: str, branch: str = "main") -> dict | None:
        """Return the most recent commit that touched `path` on `branch`."""
        r = self._request("GET", f"/repos/{self.repo}/commits",
                          params={"path": path, "sha": branch, "per_page": 1})
        items = r.json()
        return items[0] if items else None

    def list_forks(self, sort: str = "stargazers") -> Iterator[dict]:
        """List forks of the configured repo, sorted by star count by default."""
        yield from self.paginate(f"/repos/{self.repo}/forks", params={"sort": sort})

    def compare(self, base: str, head: str) -> dict:
        """`base` and `head` are revs like 'main' or 'owner:branch'.

        Returns the full /compare response (incl. ahead_by / behind_by / files /
        commits). For large diffs the API returns up to 300 files / 250 commits
        and sets `truncated=True`; callers should treat the lists as a sample.
        """
        r = self._request("GET", f"/repos/{self.repo}/compare/{base}...{head}")
        return r.json()

    def list_workflow_runs(self, workflow_file: str, status: str | None = "success",
                           branch: str | None = "main") -> Iterator[dict]:
        """Iterate workflow runs for one specific workflow file (e.g.
        'perf-benchmarks.yml'). Filters to `status` / `branch` if provided."""
        params: dict[str, Any] = {}
        if status:
            params["status"] = status
        if branch:
            params["branch"] = branch
        for page in self.paginate(
            f"/repos/{self.repo}/actions/workflows/{workflow_file}/runs",
            params=params,
        ):
            # /runs returns {"workflow_runs":[...]} not a flat list — paginate()
            # yields that dict; unpack here.
            if isinstance(page, dict) and "workflow_runs" in page:
                yield from page["workflow_runs"]

    def list_artifacts(self, run_id: int) -> Iterator[dict]:
        """List artifacts for one workflow run."""
        for page in self.paginate(f"/repos/{self.repo}/actions/runs/{run_id}/artifacts"):
            if isinstance(page, dict) and "artifacts" in page:
                yield from page["artifacts"]

    def download_artifact(self, artifact_id: int) -> bytes:
        """Download an artifact zip. The endpoint 302-redirects to a presigned
        S3 URL; httpx follows redirects by default for GET."""
        r = self._request("GET", f"/repos/{self.repo}/actions/artifacts/{artifact_id}/zip")
        return r.content

    def list_workflow_files(self, branch: str = "main") -> list[str]:
        """Return the file names under .github/workflows/ at `branch`. Used by
        the perf-benchmark scraper to discover candidate workflows without
        hardcoding their filenames."""
        r = self._request("GET", f"/repos/{self.repo}/contents/.github/workflows",
                          params={"ref": branch})
        items = r.json()
        if not isinstance(items, list):
            return []
        return [it["name"] for it in items if it.get("type") == "file"]
