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
