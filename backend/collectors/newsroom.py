"""Public newsroom / RSS collectors for AI company intelligence.

These collectors pull from publicly available RSS feeds and news pages.
They use only standard library urllib (no extra dependencies). Collection is
periodic — results reflect the last poll, not real-time streaming.
"""
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import List

from collectors.base import BaseCollector, CollectorResult

# Public RSS feeds / news URLs for AI companies. These are best-effort public
# sources; if a feed is unavailable the collector reports failure honestly.
COMPANY_SOURCES = {
    "OpenAI": {
        "url": "https://openai.com/blog/rss.xml",
        "type": "newsroom",
    },
    "Anthropic": {
        "url": "https://www.anthropic.com/news/rss.xml",
        "type": "newsroom",
    },
    "Google DeepMind": {
        "url": "https://deepmind.google/blog/rss.xml",
        "type": "newsroom",
    },
    "Microsoft AI": {
        "url": "https://azure.microsoft.com/en-us/blog/feed/",
        "type": "newsroom",
    },
    "Meta AI": {
        "url": "https://ai.meta.com/blog/rss/",
        "type": "newsroom",
    },
    "NVIDIA": {
        "url": "https://nvidianews.nvidia.com/releases.rss",
        "type": "newsroom",
    },
    "xAI": {
        "url": "https://x.ai/blog/rss.xml",
        "type": "newsroom",
    },
    "Mistral AI": {
        "url": "https://mistral.ai/news/rss.xml",
        "type": "newsroom",
    },
    "DeepSeek": {
        "url": "https://deepseek.com/blog/rss.xml",
        "type": "newsroom",
    },
    "Amazon AWS AI": {
        "url": "https://aws.amazon.com/blogs/machine-learning/feed/",
        "type": "newsroom",
    },
}


class NewsroomCollector(BaseCollector):
    """Collects intelligence events from a company public RSS/news feed."""

    def __init__(self, company: str):
        info = COMPANY_SOURCES.get(company, {"url": "", "type": "newsroom"})
        super().__init__(source_name=company, source_type=info["type"])
        self.feed_url = info["url"]

    def collect(self) -> CollectorResult:
        result = CollectorResult(source_name=self.source_name, source_type=self.source_type)
        result.mark_started()
        try:
            items = self._fetch_feed()
            events = []
            for item in items:
                events.append(self._event(
                    title=item.get("title", "Untitled"),
                    company=self.source_name,
                    category=self._guess_category(item.get("title", ""), item.get("description", "")),
                    description=item.get("description", ""),
                    source_url=item.get("link", ""),
                    publication_date=item.get("pubDate", ""),
                    evidence_snippet=item.get("description", "")[:300],
                    confidence="medium",
                    event_type="news",
                    verification_status="media",
                    strategic_importance="medium",
                ))
            result.mark_completed(events)
        except Exception as exc:  # noqa: BLE001
            result.mark_failed(str(exc))
        return result

    def _fetch_feed(self) -> List[dict]:
        if not self.feed_url:
            return []
        req = urllib.request.Request(
            self.feed_url,
            headers={"User-Agent": "CompeteIQ/1.0 (competitive intelligence)"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        root = ET.fromstring(data)
        items = []
        for item in root.findall(".//item"):
            def text(tag):
                el = item.find(tag)
                return el.text.strip() if el is not None and el.text else ""
            items.append({
                "title": text("title"),
                "description": text("description"),
                "link": text("link"),
                "pubDate": text("pubDate"),
            })
        return items

    @staticmethod
    def _guess_category(title: str, description: str) -> str:
        blob = (title + " " + description).lower()
        keywords = {
            "models": ["model", "gpt", "claude", "gemini", "llm", "release", "launch"],
            "research": ["research", "paper", "arxiv", "study", "finding"],
            "partnerships": ["partner", "partnership", "collaboration"],
            "funding": ["funding", "investment", "round", "raises"],
            "infrastructure": ["gpu", "cluster", "data center", "infrastructure", "compute"],
            "pricing": ["price", "pricing", "cost", "subscription"],
            "products": ["product", "feature", "launch", "announce"],
        }
        for category, kws in keywords.items():
            if any(k in blob for k in kws):
                return category
        return "news"


class HuggingFaceCollector(BaseCollector):
    """Collects notable model releases from Hugging Face (public API, no auth)."""

    def __init__(self):
        super().__init__(source_name="Hugging Face", source_type="huggingface")
        self.api_url = "https://huggingface.co/api/models?sort=downloads&direction=-1&limit=20"

    def collect(self) -> CollectorResult:
        result = CollectorResult(source_name=self.source_name, source_type=self.source_type)
        result.mark_started()
        try:
            import json
            req = urllib.request.Request(
                self.api_url,
                headers={"User-Agent": "CompeteIQ/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                models = json.loads(resp.read().decode())
            events = []
            for m in models[:10]:
                events.append(self._event(
                    title=f"Model trending on Hugging Face: {m.get('modelId', 'unknown')}",
                    company="Hugging Face",
                    category="models",
                    description=f"Model {m.get('modelId', 'unknown')} with {m.get('downloads', 0):,} downloads. "
                                f"Tags: {', '.join(m.get('tags', [])[:5])}.",
                    source_url=f"https://huggingface.co/{m.get('modelId', '')}",
                    publication_date=m.get("lastModified", ""),
                    confidence="medium",
                    event_type="report",
                    verification_status="media",
                    strategic_importance="low",
                ))
            result.mark_completed(events)
        except Exception as exc:  # noqa: BLE001
            result.mark_failed(str(exc))
        return result


class ArxivCollector(BaseCollector):
    """Collects recent AI papers from arXiv (public API, no auth)."""

    def __init__(self):
        super().__init__(source_name="arXiv", source_type="arxiv")
        self.api_url = ("https://export.arxiv.org/api/query?"
                        "search_query=cat:cs.AI&sortBy=submittedDate&sortOrder=descending&max_results=10")

    def collect(self) -> CollectorResult:
        result = CollectorResult(source_name=self.source_name, source_type=self.source_type)
        result.mark_started()
        try:
            import xml.etree.ElementTree as ET
            req = urllib.request.Request(
                self.api_url,
                headers={"User-Agent": "CompeteIQ/1.0"},
            )
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            root = ET.fromstring(data)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            events = []
            for entry in root.findall("a:entry", ns):
                title_el = entry.find("a:title", ns)
                summary_el = entry.find("a:summary", ns)
                link_el = entry.find("a:id", ns)
                updated_el = entry.find("a:updated", ns)
                events.append(self._event(
                    title=(title_el.text or "").strip().replace("\n", " ") if title_el is not None else "Untitled paper",
                    company="arXiv",
                    category="research",
                    description=(summary_el.text or "").strip()[:400] if summary_el is not None else "",
                    source_url=link_el.text if link_el is not None else "",
                    publication_date=(updated_el.text or "") if updated_el is not None else "",
                    confidence="medium",
                    event_type="report",
                    verification_status="media",
                    strategic_importance="low",
                ))
            result.mark_completed(events)
        except Exception as exc:  # noqa: BLE001
            result.mark_failed(str(exc))
        return result


class GitHubCollector(BaseCollector):
    """Collects notable AI releases from GitHub (public API, optional token)."""

    def __init__(self, token: str | None = None):
        super().__init__(source_name="GitHub", source_type="github")
        self.token = token
        self.api_url = ("https://api.github.com/search/repositories?"
                        "q=topic:large-language-models+topic:ai&sort=updated&order=desc&per_page=10")

    def collect(self) -> CollectorResult:
        result = CollectorResult(source_name=self.source_name, source_type=self.source_type)
        result.mark_started()
        try:
            import json
            headers = {"User-Agent": "CompeteIQ/1.0", "Accept": "application/vnd.github+json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            req = urllib.request.Request(self.api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode())
            events = []
            for repo in data.get("items", []):
                events.append(self._event(
                    title=f"GitHub repo updated: {repo.get('full_name', 'unknown')}",
                    company="GitHub",
                    category="models",
                    description=repo.get("description", "") or "AI/ML repository",
                    source_url=repo.get("html_url", ""),
                    publication_date=repo.get("updated_at", ""),
                    confidence="medium",
                    event_type="report",
                    verification_status="media",
                    strategic_importance="low",
                ))
            result.mark_completed(events)
        except Exception as exc:  # noqa: BLE001
            result.mark_failed(str(exc))
        return result
