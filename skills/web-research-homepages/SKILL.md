---
name: web-research-homepages
description: 联网检索当前、可溯源的信息，并提炼简洁结论。当用户要求查找、浏览、核实、研究或获取在线信息时使用；当主题可能有时效性或不确定性时使用；当需要引用链接、来源归因或实体背景时使用。对于人物、公司、组织、品牌、产品所有者、创始人、高管、公众人物或企业相关搜索，需要额外识别并返回最合适的官方个人主页、公司网站、权威资料页或百科资料页。
---

# Web Search And Homepage Identification

## Workflow

1. Search directly unless the query target is too ambiguous or likely to refer to multiple entities.
2. Use web search for current facts, recommendations, prices, rules, company or person details, and any information that may have changed.
3. Prefer primary and authoritative sources: official websites, personal domains, company websites, regulator filings, institutional profiles, reliable databases, direct publications, and encyclopedia pages.
4. Cross-check important facts with at least two independent sources when possible, especially identity, job titles, affiliations, dates, and claims about people or companies.
5. Return links for the sources used. Clearly label conclusions that are inferred from sources.

## Homepage And Source Priority

When the target is a person or business, include an `官方主页` field in the answer.

Person source priority:

1. Personal domain, personal website, portfolio, or site controlled by the person.
2. Official profile from an employer, university, lab, publisher, foundation, league, team, or government institution.
3. Encyclopedia pages such as Wikipedia, 百度百科, or Britannica when no reliable official page is available.
4. Verified social or profile page only when no personal, institutional, or encyclopedia page is available.

Company source priority:

1. Official company or organization website.
2. Official product or brand site owned by the company.
3. Regulator, exchange, app store, marketplace profile, or encyclopedia page when no official site is available.

Do not treat directories, SEO pages, sales-lead databases, fan pages, or unrelated social accounts as official homepages. If no reliable homepage or acceptable encyclopedia page is found, write `官方主页：未找到` and briefly say what was checked.

## Output

Answer in the user's language unless they ask otherwise. Keep the answer concise unless the task calls for a deeper report.

General search answers should include:

- `摘要`: the direct answer or key findings.
- `详情`: relevant evidence, dates, caveats, and comparisons.
- `来源`: linked sources.

Person or company search answers should include:

- `官方主页`: the best official URL, acceptable encyclopedia URL, or `未找到`.
- `身份核验`: one sentence explaining why this is the correct person or company when there is same-name risk.
- `摘要`, `详情`, and `来源`.

## Quality Rules

- Distinguish official sources, media reports, databases, encyclopedia pages, and opinion content.
- Do not overstate uncertain facts.
- Preserve exact dates for recent or time-sensitive information.
- If sources conflict, say so instead of smoothing over the difference.
- Respect copyright limits: use short excerpts only, and summarize the rest.
