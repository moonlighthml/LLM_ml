from app.models.tools import WebSearchRequest, WebSearchResponse, WebSearchResult


async def search_web(request: WebSearchRequest) -> WebSearchResponse:
    return WebSearchResponse(
        query=request.query,
        results=[
            WebSearchResult(
                title="尚未配置网页搜索供应商",
                url="https://github.com/moonlighthml/LLM_ml",
                snippet=(
                    "该接口目前是为后续网页搜索供应商预留的占位实现。"
                    "拿到搜索 API 密钥后，可以在这里新增供应商适配器。"
                ),
            )
        ][: request.limit],
        note="占位响应：当前尚未配置真实网页搜索 API。",
    )
