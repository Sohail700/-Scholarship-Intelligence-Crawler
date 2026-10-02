from __future__ import annotations

import hashlib
import io
import time
from dataclasses import dataclass
from typing import List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader

from .config import SETTINGS


@dataclass
class FetchResult:
    url: str
    status_code: int
    content_type: str
    text: str
    content_hash: str
    links: List[str]
    final_url: str


class Fetcher:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": SETTINGS.user_agent})

    def fetch(self, url: str) -> FetchResult:
        time.sleep(SETTINGS.crawl_delay_seconds)
        response = self.session.get(
            url,
            timeout=SETTINGS.request_timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        raw = response.content
        content_hash = hashlib.sha256(raw).hexdigest()
        content_type = response.headers.get("content-type", "").lower()
        if "pdf" in content_type or response.url.lower().endswith(".pdf"):
            text = self._pdf_text(raw)
            links: List[str] = []
        else:
            soup = BeautifulSoup(response.text, "html.parser")
            text = self._visible_text(soup)
            links = [urljoin(response.url, a.get("href")) for a in soup.find_all("a", href=True)]
        return FetchResult(
            url=url,
            status_code=response.status_code,
            content_type=content_type,
            text=text,
            content_hash=content_hash,
            links=links,
            final_url=response.url,
        )

    @staticmethod
    def _visible_text(soup: BeautifulSoup) -> str:
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        text = soup.get_text("\n")
        lines = [" ".join(line.split()) for line in text.splitlines()]
        return "\n".join(line for line in lines if line)

    @staticmethod
    def _pdf_text(raw: bytes) -> str:
        reader = PdfReader(io.BytesIO(raw))
        chunks: List[str] = []
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
        return "\n".join(chunks)
