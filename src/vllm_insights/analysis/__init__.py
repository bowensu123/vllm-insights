"""Intelligent analyses on top of the cached GitHub data.

Each submodule produces one table or one homepage section:

  pr_issue_links  — #5  PR ↔ Issue link mining (Fixes/Closes parsing)
  release_diff    — #4  release-to-release file-change drift by directory
  embeddings      — shared: OpenAI text embedding wrapper + cluster runner
  topics          — #1+#2 cluster PRs / issues + LLM-label the clusters
  benchmarks      — #6  perf workflow artifact scraping
"""
