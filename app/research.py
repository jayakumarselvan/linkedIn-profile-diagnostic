import asyncio
from collections.abc import Iterable

import httpx
from bs4 import BeautifulSoup

from app.config import Settings
from app.models import DiagnosticRequest, Source
from app.source_utils import is_low_value_url, looks_primary

USER_AGENT = (
    "Mozilla/5.0 (compatible; LinkedInProfileDiagnosticBot/0.1; "
    "+https://example.local/public-profile-diagnostic)"
)


class Researcher:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def collect_sources(self, request: DiagnosticRequest) -> tuple[list[Source], list[str]]:
        warnings: list[str] = []
        discovered_urls: list[str] = []

        search_query = self._build_query(request)
        try:
            search_sources = await self._search(search_query)
        except Exception as exc:
            warnings.append(
                "Search provider failed. Paste public source URLs manually or check network/API "
                f"configuration. Error: {type(exc).__name__}: {exc}"
            )
            search_sources = []
        discovered_urls.extend(source.url for source in search_sources)
        discovered_urls.extend(str(url) for url in request.manual_source_urls)

        if not discovered_urls:
            warnings.append(
                "No search provider is configured and no manual sources were supplied. "
                "Add BRAVE_SEARCH_API_KEY, TAVILY_API_KEY, SERPAPI_API_KEY, or paste source URLs."
            )

        urls = self._dedupe_urls(discovered_urls)
        urls = [url for url in urls if not is_low_value_url(url)][:10]

        fetched = await self._fetch_many(urls, request)
        by_url = {source.url: source for source in fetched}
        for source in search_sources:
            if source.url in by_url and source.snippet:
                by_url[source.url].snippet = source.snippet
        return list(by_url.values()), warnings

    def _build_query(self, request: DiagnosticRequest) -> str:
        parts = [request.subject_name]
        if request.company_name:
            parts.append(request.company_name)
        parts.extend(["UAE founder CEO fund manager public profile"])
        return " ".join(parts)

    async def _search(self, query: str) -> list[Source]:
        if self.settings.brave_search_api_key:
            return await self._search_brave(query)
        if self.settings.tavily_api_key:
            return await self._search_tavily(query)
        if self.settings.serpapi_api_key:
            return await self._search_serpapi(query)
        return []

    async def _search_brave(self, query: str) -> list[Source]:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": self.settings.brave_search_api_key or "",
        }
        params = {"q": query, "count": 8, "country": "AE", "search_lang": "en"}
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params=params,
                headers=headers,
            )
            response.raise_for_status()
        web = response.json().get("web", {}).get("results", [])
        return [
            Source(url=item["url"], title=item.get("title"), snippet=item.get("description"))
            for item in web
            if item.get("url")
        ]

    async def _search_tavily(self, query: str) -> list[Source]:
        payload = {
            "api_key": self.settings.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": 8,
        }
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.post("https://api.tavily.com/search", json=payload)
            response.raise_for_status()
        return [
            Source(url=item["url"], title=item.get("title"), snippet=item.get("content"))
            for item in response.json().get("results", [])
            if item.get("url")
        ]

    async def _search_serpapi(self, query: str) -> list[Source]:
        params = {
            "api_key": self.settings.serpapi_api_key,
            "engine": "google",
            "q": query,
            "num": 8,
            "gl": "ae",
        }
        async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
            response = await client.get("https://serpapi.com/search.json", params=params)
            response.raise_for_status()
        return [
            Source(url=item["link"], title=item.get("title"), snippet=item.get("snippet"))
            for item in response.json().get("organic_results", [])
            if item.get("link")
        ]

    async def _fetch_many(self, urls: Iterable[str], request: DiagnosticRequest) -> list[Source]:
        tasks = [self._fetch(url, request) for url in urls]
        if not tasks:
            return []
        return await asyncio.gather(*tasks)

    async def _fetch(self, url: str, request: DiagnosticRequest) -> Source:
        is_primary = looks_primary(url, request.subject_name, request.company_name)
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                headers={"User-Agent": USER_AGENT},
                timeout=self.settings.request_timeout_seconds,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            return Source(url=url, is_primary=is_primary, error=f"{type(exc).__name__}: {exc}")

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return Source(
                url=url,
                is_primary=is_primary,
                error=f"Unsupported content type: {content_type or 'unknown'}",
            )

        title, text = self._extract_text(response.text)
        return Source(
            url=str(response.url),
            title=title,
            is_primary=is_primary,
            extracted_text=text[: self.settings.max_source_chars],
        )

    def _extract_text(self, html: str) -> tuple[str | None, str]:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "svg"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        text = " ".join(soup.get_text(" ").split())
        return title, text

    def _dedupe_urls(self, urls: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for url in urls:
            normalized = str(url).split("#", 1)[0].rstrip("/")
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(normalized)
        return unique
