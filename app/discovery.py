from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from urllib.parse import urlparse

from .fetcher import Fetcher

KEYWORDS = (
    "scholarship",
    "fellowship",
    "financial aid",
    "funding",
    "stipend",
    "student support",
    "education assistance",
    "education grant",
    "apply",
    "scheme",
)


def load_seeds(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def is_allowed(url: str, official_domain: str) -> bool:
    host = canonical_host(url)
    official = official_domain.lower().removeprefix("www.")
    return host == official or host.endswith("." + official)


def link_priority(url: str) -> int:
    value = url.lower()
    score = 0
    for word in KEYWORDS:
        if word in value:
            score += 2
    if value.endswith(".pdf"):
        score += 1
    return score


def discover(seed: dict, fetcher: Fetcher) -> list[tuple[str, int]]:
    max_depth = min(int(seed.get("max_depth", 2)), 5)
    queue = deque([(seed["url"], 0)])
    seen: set[str] = set()
    discovered: list[tuple[str, int]] = []

    while queue and len(seen) < 200:
        url, depth = queue.popleft()
        if url in seen or not is_allowed(url, seed["official_domain"]):
            continue
        seen.add(url)
        discovered.append((url, depth))
        if depth >= max_depth:
            continue
        try:
            result = fetcher.fetch(url)
        except Exception:
            continue
        links = sorted(set(result.links), key=link_priority, reverse=True)
        for link in links:
            if link not in seen and is_allowed(link, seed["official_domain"]):
                queue.append((link, depth + 1))
    return discovered
