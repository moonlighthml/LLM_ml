from app.models.tools import WebSearchRequest, WebSearchResponse, WebSearchResult

FIXED_HOMEPAGE_QUERY = "搜索科比的个人主页"


async def search_web(request: WebSearchRequest) -> WebSearchResponse:
    if request.query.strip() == FIXED_HOMEPAGE_QUERY:
        results = [
            WebSearchResult(
                title="Kobe Bryant - NBA 官方资料页",
                url="https://www.nba.com/stats/player/977/career",
                snippet="NBA 官方球员资料页，包含 Kobe Bryant 的职业生涯数据与基础信息。",
                source="固定测试候选",
            ),
            WebSearchResult(
                title="Kobe Bryant - Wikipedia",
                url="https://en.wikipedia.org/wiki/Kobe_Bryant",
                snippet="维基百科条目，适合作为公开人物基础资料候选来源，不等同于个人官方网站。",
                source="固定测试候选",
            ),
            WebSearchResult(
                title="Kobe Bryant - Basketball-Reference",
                url="https://www.basketball-reference.com/players/b/bryanko01.html",
                snippet="Basketball-Reference 球员资料页，包含 Kobe Bryant 的详细篮球数据。",
                source="固定测试候选",
            ),
        ][: request.limit]
        return WebSearchResponse(
            query=request.query,
            results=results,
            note="固定输入测试结果：科比已故，当前返回权威资料页和公开资料候选，而不是个人官网。",
        )

    return WebSearchResponse(
        query=request.query,
        results=[
            WebSearchResult(
                title="尚未配置真实网页搜索供应商",
                url="https://github.com/moonlighthml/LLM_ml",
                snippet=(
                    "该接口目前是为后续网页搜索供应商预留的占位实现。"
                    "拿到搜索 API 密钥后，可以在这里新增供应商适配器。"
                ),
            )
        ][: request.limit],
        note="占位响应：当前尚未配置真实网页搜索 API。",
    )
