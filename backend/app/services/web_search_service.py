"""
Web search helper.

Uses SerpAPI/Google first when configured, then falls back to free
DuckDuckGo and RSS sources.
"""

from __future__ import annotations

import asyncio
import html
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import requests

from app.services.runtime_config_service import runtime_config_service

logger = logging.getLogger(__name__)


class DuckDuckGoSearchService:
    """SerpAPI-first search client with DuckDuckGo/RSS fallback."""

    SERPAPI_URL = "https://serpapi.com/search.json"
    SEARCH_URL = "https://duckduckgo.com/html/"
    LITE_URL = "https://lite.duckduckgo.com/lite/"
    INSTANT_URL = "https://api.duckduckgo.com/"
    GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
    BING_NEWS_RSS_URL = "https://www.bing.com/news/search"

    def should_search(self, text: str) -> bool:
        query = text.lower().strip()
        if not query:
            return False

        explicit = [
            "search web",
            "web search",
            "search online",
            "look up",
            "google",
            "duckduckgo",
            "latest",
            "current",
            "today",
            "news",
            "recent",
            "right now",
        ]
        return any(phrase in query for phrase in explicit)

    def _is_news_query(self, text: str) -> bool:
        query = text.lower()
        return any(term in query for term in ("news", "latest", "recent", "today", "current", "politics"))

    def _clean_url(self, url: str) -> str:
        url = html.unescape(url)
        parsed = urlparse(url)
        if parsed.path.startswith("/l/"):
            uddg = parse_qs(parsed.query).get("uddg")
            if uddg:
                return unquote(uddg[0])
        return url

    def _parse_results(self, markup: str, limit: int) -> list[dict[str, str]]:
        html_pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(?P<snippet>.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )
        lite_pattern = re.compile(
            r'<a[^>]+rel="nofollow"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>.*?'
            r'<td[^>]+class="result-snippet"[^>]*>(?P<snippet>.*?)</td>',
            re.IGNORECASE | re.DOTALL,
        )

        results: list[dict[str, str]] = []
        for pattern in (html_pattern, lite_pattern):
            for match in pattern.finditer(markup):
                title = re.sub(r"<.*?>", "", match.group("title"))
                snippet = re.sub(r"<.*?>", "", match.group("snippet"))
                url = self._clean_url(match.group("url"))
                item = {
                    "title": html.unescape(title).strip(),
                    "url": url.strip(),
                    "snippet": html.unescape(snippet).strip(),
                }
                if item["title"] and item["url"] and item not in results:
                    results.append(item)
                if len(results) >= limit:
                    return results

        return results

    def _parse_instant_answer(self, payload: dict[str, Any], limit: int) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []

        abstract = str(payload.get("AbstractText") or "").strip()
        abstract_url = str(payload.get("AbstractURL") or "").strip()
        heading = str(payload.get("Heading") or "DuckDuckGo result").strip()
        if abstract and abstract_url:
            results.append({"title": heading, "url": abstract_url, "snippet": abstract})

        related = payload.get("RelatedTopics") or []
        for item in related:
            if "Topics" in item:
                related.extend(item.get("Topics") or [])
                continue
            text = str(item.get("Text") or "").strip()
            url = str(item.get("FirstURL") or "").strip()
            if text and url:
                title = text.split(" - ", 1)[0][:120]
                results.append({"title": title, "url": url, "snippet": text})
            if len(results) >= limit:
                break

        return results[:limit]

    def _parse_rss_results(self, markup: str, limit: int) -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        root = ET.fromstring(markup)

        for item in root.findall(".//item"):
            title = item.findtext("title") or ""
            url = item.findtext("link") or ""
            snippet = item.findtext("description") or ""
            published = item.findtext("pubDate") or ""

            clean_snippet = re.sub(r"<.*?>", " ", snippet)
            clean_snippet = re.sub(r"\s+", " ", html.unescape(clean_snippet)).strip()

            item_result = {
                "title": html.unescape(title).strip(),
                "url": html.unescape(url).strip(),
                "snippet": clean_snippet[:280],
                "published": published.strip(),
            }
            if item_result["title"] and item_result["url"] and item_result not in results:
                results.append(item_result)
            if len(results) >= limit:
                break

        return results

    def _html_request(self, url: str, query: str, limit: int) -> list[dict[str, str]]:
        response = requests.get(
            url,
            params={"q": query},
            headers={
                "User-Agent": "Mozilla/5.0 AgentCoolie/2.0",
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=10,
        )
        response.raise_for_status()
        return self._parse_results(response.text, limit)

    def _instant_request(self, query: str, limit: int) -> list[dict[str, str]]:
        response = requests.get(
            self.INSTANT_URL,
            params={"q": query, "format": "json", "no_redirect": "1", "no_html": "1"},
            headers={"User-Agent": "Mozilla/5.0 AgentCoolie/2.0"},
            timeout=10,
        )
        response.raise_for_status()
        return self._parse_instant_answer(response.json(), limit)

    def _google_news_request(self, query: str, limit: int) -> list[dict[str, str]]:
        response = requests.get(
            self.GOOGLE_NEWS_RSS_URL,
            params={"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"},
            headers={"User-Agent": "Mozilla/5.0 AgentCoolie/2.0"},
            timeout=10,
        )
        response.raise_for_status()
        return self._parse_rss_results(response.text, limit)

    def _bing_news_request(self, query: str, limit: int) -> list[dict[str, str]]:
        response = requests.get(
            self.BING_NEWS_RSS_URL,
            params={"q": query, "format": "rss"},
            headers={"User-Agent": "Mozilla/5.0 AgentCoolie/2.0"},
            timeout=10,
        )
        response.raise_for_status()
        return self._parse_rss_results(response.text, limit)

    def _serpapi_request(self, query: str, limit: int, api_key: str | None) -> list[dict[str, str]]:
        if not api_key:
            return []

        params: dict[str, str | int] = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": limit,
            "hl": "en",
            "gl": "in",
        }
        if self._is_news_query(query):
            params["tbm"] = "nws"

        response = requests.get(
            self.SERPAPI_URL,
            params=params,
            headers={"User-Agent": "AgentCoolie/2.0"},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()

        raw_results = (
            payload.get("news_results")
            or payload.get("organic_results")
            or payload.get("top_stories")
            or []
        )
        results: list[dict[str, str]] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("link") or item.get("url") or "").strip()
            snippet = str(item.get("snippet") or item.get("source") or "").strip()
            published = str(item.get("date") or item.get("published") or "").strip()
            if title and url:
                result = {"title": title, "url": url, "snippet": snippet}
                if published:
                    result["published"] = published
                results.append(result)
            if len(results) >= limit:
                break

        return self._dedupe_results(results, limit)

    async def search(self, query: str, limit: int = 5) -> list[dict[str, str]]:
        serpapi_key = await runtime_config_service.get_secret("SERPAPI_API_KEY")

        def _request() -> list[dict[str, str]]:
            attempts = []
            if serpapi_key:
                attempts.append(lambda: self._serpapi_request(query, limit, serpapi_key))

            attempts.extend([
                lambda: self._html_request(self.SEARCH_URL, query, limit),
                lambda: self._html_request(self.LITE_URL, query, limit),
            ])
            if self._is_news_query(query):
                attempts.extend(
                    [
                        lambda: self._google_news_request(query, limit),
                        lambda: self._bing_news_request(query, limit),
                    ]
                )
            attempts.append(lambda: self._instant_request(query, limit))

            last_error: Exception | None = None
            for attempt in attempts:
                try:
                    results = attempt()
                    if results:
                        return self._dedupe_results(results, limit)
                except Exception as e:
                    last_error = e
            if last_error:
                raise last_error
            return []

        try:
            return await asyncio.to_thread(_request)
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return []

    def _dedupe_results(self, results: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
        deduped: list[dict[str, str]] = []
        seen_urls: set[str] = set()
        for result in results:
            url = str(result.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            deduped.append(result)
            if len(deduped) >= limit:
                break
        return deduped

    def format_for_prompt(self, results: list[dict[str, Any]], attempted: bool = False) -> str:
        if not results:
            if attempted:
                return (
                    "Web search was attempted, but no live search results were available. "
                    "If the user needs current information, say that live search failed and ask them to retry."
                )
            return "No web search was requested."

        lines = []
        for index, result in enumerate(results, start=1):
            title = str(result.get("title") or "").strip()
            url = str(result.get("url") or "").strip()
            snippet = str(result.get("snippet") or "").strip()
            published = str(result.get("published") or "").strip()
            date_line = f"\nPublished: {published}" if published else ""
            lines.append(f"{index}. {title}\nURL: {url}{date_line}\nSnippet: {snippet}")
        return "\n\n".join(lines)


web_search_service = DuckDuckGoSearchService()
