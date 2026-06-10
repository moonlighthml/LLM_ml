import html
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx

from app.core.config import settings
from app.models.tools import WebSearchRequest, WebSearchResponse, WebSearchResult


KNOWN_ENTITY_QUERY_ALIASES = {
    "科比": ["Kobe Bryant", "Kobe Bryant official homepage", "Kobe Bryant NBA official profile"],
    "科比布莱恩特": ["Kobe Bryant", "Kobe Bryant official homepage", "Kobe Bryant NBA official profile"],
    "科比·布莱恩特": ["Kobe Bryant", "Kobe Bryant official homepage", "Kobe Bryant NBA official profile"],
}
HOMEPAGE_INTENT_TERMS = ["主页", "官网", "官方", "profile", "homepage", "official", "检索", "搜索", "查找"]


SEARCH_WEB_TOOL_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Search the public web with DuckDuckGo and return result titles, URLs, and snippets.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The web search query. Include enough keywords to identify the entity or current fact.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}


class _DuckDuckGoHTMLParser(HTMLParser):
    def __init__(self, limit: int) -> None:
        super().__init__()
        self.limit = limit
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._capture_title = False
        self._capture_snippet = False
        self._title_parts: list[str] = []
        self._snippet_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        class_name = attrs_dict.get("class", "")
        if tag == "a" and "result__a" in class_name:
            self._flush_current()
            self._current = {"title": "", "url": self._normalize_url(attrs_dict.get("href", "")), "snippet": ""}
            self._capture_title = True
            self._title_parts = []
        elif tag in {"a", "div"} and "result__snippet" in class_name and self._current is not None:
            self._capture_snippet = True
            self._snippet_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._capture_title and self._current is not None:
            self._current["title"] = self._clean(" ".join(self._title_parts))
            self._capture_title = False
        elif tag in {"a", "div"} and self._capture_snippet and self._current is not None:
            self._current["snippet"] = self._clean(" ".join(self._snippet_parts))
            self._capture_snippet = False

    def handle_data(self, data: str) -> None:
        if self._capture_title:
            self._title_parts.append(data)
        if self._capture_snippet:
            self._snippet_parts.append(data)

    def close(self) -> None:
        super().close()
        self._flush_current()

    def _flush_current(self) -> None:
        if len(self.results) >= self.limit:
            return
        if self._current and self._current.get("title") and self._current.get("url"):
            self.results.append(self._current)
        self._current = None

    @staticmethod
    def _clean(value: str) -> str:
        return re.sub(r"\s+", " ", html.unescape(value)).strip()

    @staticmethod
    def _normalize_url(value: str) -> str:
        value = html.unescape(value)
        parsed = urlparse(value)
        if parsed.path == "/l/":
            uddg = parse_qs(parsed.query).get("uddg", [""])[0]
            if uddg:
                return unquote(uddg)
        return value


def _extract_candidates(data: Any) -> Any:
    if not isinstance(data, dict):
        return data

    if isinstance(data.get("references"), list):
        return data["references"]

    data_block = data.get("data")
    if isinstance(data_block, dict):
        web_pages = data_block.get("webPages")
        if isinstance(web_pages, dict) and isinstance(web_pages.get("value"), list):
            return web_pages["value"]
        return data_block

    return data


def _extract_results(data: Any, limit: int) -> list[WebSearchResult]:
    candidates = _extract_candidates(data)
    if isinstance(candidates, dict):
        for key in ["results", "items", "documents", "search_results", "value", "references"]:
            value = candidates.get(key)
            if isinstance(value, list):
                candidates = value
                break
            if isinstance(value, dict):
                nested = value.get("results") or value.get("items") or value.get("documents") or value.get("value")
                if isinstance(nested, list):
                    candidates = nested
                    break

    if not isinstance(candidates, list):
        return []

    results: list[WebSearchResult] = []
    for item in candidates[:limit]:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("name") or item.get("site_name") or "Untitled result"
        url = item.get("url") or item.get("link") or item.get("href") or item.get("source_url")
        snippet = item.get("snippet") or item.get("content") or item.get("summary") or item.get("description") or ""
        source = item.get("source") or item.get("site") or item.get("siteName") or item.get("website") or "Gitee Search"
        if url:
            results.append(WebSearchResult(title=str(title), url=str(url), snippet=str(snippet), source=str(source)))
    return results


def _build_gitee_payload(request: WebSearchRequest) -> dict[str, Any]:
    if settings.gitee_web_search_path.strip("/").endswith("web-search-v2"):
        return {"content": request.query}
    return {"query": request.query, "summary": True, "count": request.limit}


def _gitee_error_note(exc: httpx.HTTPStatusError) -> str:
    try:
        body = exc.response.json()
    except ValueError:
        body = exc.response.text
    if isinstance(body, dict):
        detail = body.get("error") or body.get("message") or body.get("msg") or str(body)
    else:
        detail = str(body).strip()
    if detail:
        return f"Gitee web search returned HTTP {exc.response.status_code}: {detail}"
    return f"Gitee web search returned HTTP {exc.response.status_code}."


async def _search_duckduckgo(request: WebSearchRequest) -> WebSearchResponse:
    query_variants = _duckduckgo_query_variants(request.query)
    merged_results: list[WebSearchResult] = []
    notes: list[str] = []
    seen_urls: set[str] = set()

    for query in query_variants:
        response = await _search_duckduckgo_once(WebSearchRequest(query=query, limit=request.limit))
        notes.append(f"{query}: {response.note}")
        for result in response.results:
            normalized_url = result.url.rstrip("/")
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)
            merged_results.append(result)
        if len(merged_results) >= request.limit and _has_authoritative_homepage(merged_results):
            break

    if not merged_results:
        for query in query_variants:
            response = await _search_duckduckgo_instant_answer(WebSearchRequest(query=query, limit=request.limit))
            notes.append(f"{query}: {response.note}")
            for result in response.results:
                normalized_url = result.url.rstrip("/")
                if normalized_url in seen_urls:
                    continue
                seen_urls.add(normalized_url)
                merged_results.append(result)
            if merged_results:
                break

    ranked_results = sorted(merged_results, key=_result_rank, reverse=True)[: request.limit]
    return WebSearchResponse(
        query=request.query,
        results=ranked_results,
        note="Searched DuckDuckGo." if ranked_results else "; ".join(notes) or "DuckDuckGo returned no parseable results.",
    )


def _duckduckgo_query_variants(query: str) -> list[str]:
    variants = [query]
    normalized = re.sub(r"\s+", "", query.lower())
    has_homepage_intent = any(term in query.lower() for term in HOMEPAGE_INTENT_TERMS)

    if has_homepage_intent:
        variants.append(f"{query} 官方主页 官网 official website official profile")

    for alias, alias_queries in KNOWN_ENTITY_QUERY_ALIASES.items():
        if alias.lower() in normalized:
            variants.extend(alias_queries)

    deduped: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        if variant not in seen:
            seen.add(variant)
            deduped.append(variant)
    return deduped


def _has_authoritative_homepage(results: list[WebSearchResult]) -> bool:
    return any(_result_rank(result) >= 50 for result in results)


def _result_rank(result: WebSearchResult) -> int:
    url = result.url.lower()
    hostname = urlparse(url).hostname or ""
    title = result.title.lower()
    rank = 0
    if any(
        _hostname_matches(hostname, domain)
        for domain in ["kobebryant.com", "nba.com", "nike.com", "mambaandmambacita.org"]
    ):
        rank += 60
    if any(term in title for term in ["official", "nba.com", "nike.com", "profile"]):
        rank += 20
    if any(_hostname_matches(hostname, domain) for domain in ["wikipedia.org", "baike.baidu.com", "britannica.com"]):
        rank += 25
    if any(_hostname_matches(hostname, domain) for domain in ["docs.pingcode.com", "stat-nba.com"]):
        rank -= 30
    return rank


def _hostname_matches(hostname: str, domain: str) -> bool:
    return hostname == domain or hostname.endswith(f".{domain}")


async def _search_duckduckgo_once(request: WebSearchRequest) -> WebSearchResponse:
    try:
        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; LLM_ml/1.0)"},
        ) as client:
            response = await client.get("https://html.duckduckgo.com/html/", params={"q": request.query})
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return WebSearchResponse(
            query=request.query,
            results=[],
            note=f"DuckDuckGo search returned HTTP {exc.response.status_code}.",
        )
    except Exception as exc:
        return WebSearchResponse(query=request.query, results=[], note=f"DuckDuckGo search failed: {exc}")

    parser = _DuckDuckGoHTMLParser(request.limit)
    parser.feed(response.text)
    parser.close()

    results = [
        WebSearchResult(
            title=item["title"],
            url=item["url"],
            snippet=item.get("snippet", ""),
            source="DuckDuckGo",
        )
        for item in parser.results[: request.limit]
    ]
    return WebSearchResponse(
        query=request.query,
        results=results,
        note="Searched DuckDuckGo." if results else "DuckDuckGo returned no parseable results.",
    )


async def _search_duckduckgo_instant_answer(request: WebSearchRequest) -> WebSearchResponse:
    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": request.query, "format": "json", "no_html": "1", "skip_disambig": "1"},
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        return WebSearchResponse(
            query=request.query,
            results=[],
            note=f"DuckDuckGo Instant Answer returned HTTP {exc.response.status_code}.",
        )
    except Exception as exc:
        return WebSearchResponse(query=request.query, results=[], note=f"DuckDuckGo Instant Answer failed: {exc}")

    results: list[WebSearchResult] = []
    heading = data.get("Heading") or request.query
    official_website = data.get("OfficialWebsite")
    official_domain = data.get("OfficialDomain")
    abstract_text = data.get("AbstractText") or ""
    if official_website:
        results.append(
            WebSearchResult(
                title=f"{heading} official website",
                url=str(official_website),
                snippet=abstract_text or f"Official website listed by DuckDuckGo: {official_domain or official_website}",
                source="DuckDuckGo Instant Answer",
            )
        )

    abstract_url = data.get("AbstractURL")
    abstract_source = data.get("AbstractSource") or "DuckDuckGo Instant Answer"
    if abstract_url:
        results.append(
            WebSearchResult(
                title=f"{heading} - {abstract_source}",
                url=str(abstract_url),
                snippet=abstract_text,
                source=str(abstract_source),
            )
        )

    return WebSearchResponse(
        query=request.query,
        results=results[: request.limit],
        note="Searched DuckDuckGo Instant Answer." if results else "DuckDuckGo Instant Answer returned no entity result.",
    )


async def _search_gitee(request: WebSearchRequest) -> WebSearchResponse:
    endpoint = f"{settings.gitee_ai_base_url.rstrip('/')}/{settings.gitee_web_search_path.strip('/')}"
    payload = _build_gitee_payload(request)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {settings.gitee_ai_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        return WebSearchResponse(query=request.query, results=[], note=_gitee_error_note(exc))
    except Exception as exc:
        return WebSearchResponse(query=request.query, results=[], note=f"Gitee web search failed: {exc}")

    results = _extract_results(data, request.limit)
    return WebSearchResponse(
        query=request.query,
        results=results,
        note="Searched Gitee web search." if results else "Gitee web search returned no parseable results.",
    )


async def search_web(request: WebSearchRequest) -> WebSearchResponse:
    return await _search_duckduckgo(request)
