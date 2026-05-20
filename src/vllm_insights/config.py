import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    github_token: str
    repo: str
    db_path: Path

    @property
    def owner(self) -> str:
        return self.repo.split("/")[0]

    @property
    def name(self) -> str:
        return self.repo.split("/")[1]


def load_settings(require_token: bool = False) -> Settings:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if require_token and (not token or token.startswith("ghp_xxx")):
        raise RuntimeError("GITHUB_TOKEN not set. Copy .env.example to .env and fill it in.")
    repo = os.getenv("GITHUB_REPO", "vllm-project/vllm").strip()
    db_path = Path(os.getenv("DB_PATH", "./data/insights.sqlite")).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return Settings(github_token=token, repo=repo, db_path=db_path)
