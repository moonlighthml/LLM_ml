from typing import Any

import httpx

from app.core.config import settings
from app.models.tools import WebSearchRequest, WebSearchResponse, WebSearchResult


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
        title = item.get("title") or item.get("name") or item.get("site_name") or "未命名结果"
        url = item.get("url") or item.get("link") or item.get("href") or item.get("source_url")
        snippet = item.get("snippet") or item.get("content") or item.get("summary") or item.get("description") or ""
        source = item.get("source") or item.get("site") or item.get("siteName") or item.get("website") or "Gitee 搜索"
        if url:
            results.append(WebSearchResult(title=str(title), url=str(url), snippet=str(snippet), source=str(source)))
    return results


def _build_payload(request: WebSearchRequest) -> dict[str, Any]:
    if settings.gitee_web_search_path.strip("/").endswith("web-search-v2"):
        return {"content": request.query}
    return {"query": request.query, "summary": True, "count": request.limit}


def _error_note(exc: httpx.HTTPStatusError) -> str:
    try:
        body = exc.response.json()
    except ValueError:
        body = exc.response.text
    if isinstance(body, dict):
        detail = body.get("error") or body.get("message") or body.get("msg") or str(body)
    else:
        detail = str(body).strip()
    if detail:
        return f"Gitee 网页检索接口返回错误：HTTP {exc.response.status_code}，{detail}"
    return f"Gitee 网页检索接口返回错误：HTTP {exc.response.status_code}。"


async def search_web(request: WebSearchRequest) -> WebSearchResponse:
    if not settings.gitee_ai_token:
        return WebSearchResponse(
            query=request.query,
            results=[],
            note="未配置 GITEE_AI_TOKEN，无法执行真实网页检索。",
        )

    endpoint = f"{settings.gitee_ai_base_url.rstrip('/')}/{settings.gitee_web_search_path.strip('/')}"
    payload = _build_payload(request)

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
        return WebSearchResponse(
            query=request.query,
            results=[],
            note=_error_note(exc),
        )
    except Exception as exc:
        return WebSearchResponse(
            query=request.query,
            results=[],
            note=f"Gitee 网页检索调用失败：{exc}",
        )

    results = _extract_results(data, request.limit)
    return WebSearchResponse(
        query=request.query,
        results=results,
        note="已调用 Gitee 网页检索接口。" if results else "Gitee 网页检索未返回可解析结果。",
    )
