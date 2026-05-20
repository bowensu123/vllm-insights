"""Parse vLLM release-notes markdown into (section -> [items])."""
import re
from typing import Iterable

HEADING_RE = re.compile(r"^#{1,4}\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^\s*[-*+]\s+(.+?)\s*$")


def parse_sections(body: str | None) -> dict[str, list[str]]:
    """Return {section_title: [bullet_text, ...]}. Bullets outside any heading go under "_intro"."""
    if not body:
        return {}
    sections: dict[str, list[str]] = {}
    current = "_intro"
    for raw in body.splitlines():
        line = raw.rstrip()
        h = HEADING_RE.match(line)
        if h:
            current = h.group(1).strip().rstrip(":")
            sections.setdefault(current, [])
            continue
        b = BULLET_RE.match(line)
        if b:
            sections.setdefault(current, []).append(_clean(b.group(1)))
    return {k: v for k, v in sections.items() if v}


def _clean(text: str) -> str:
    # strip PR refs like (#12345) and trailing whitespace
    text = re.sub(r"\s*\(#\d+\)\s*$", "", text)
    return text.strip()


def flatten(sections: dict[str, list[str]]) -> Iterable[tuple[str, str]]:
    for section, items in sections.items():
        for item in items:
            yield section, item
