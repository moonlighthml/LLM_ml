from app.models.tools import WebSearchRequest, WebSearchResponse, WebSearchResult


async def search_web(request: WebSearchRequest) -> WebSearchResponse:
    return WebSearchResponse(
        query=request.query,
        results=[
            WebSearchResult(
                title="Web search provider not configured",
                url="https://github.com/moonlighthml/LLM_ml",
                snippet=(
                    "This endpoint is intentionally reserved for a future search provider. "
                    "Add a provider adapter here when a search API key is available."
                ),
            )
        ][: request.limit],
        note="Placeholder response. No live web search API is configured yet.",
    )

