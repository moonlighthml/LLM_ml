# 项目导览与使用手册

这份文档面向“通过 vibe coding 让 AI 继续生成和修改代码”的使用方式。目标不是讲完所有技术细节，而是帮你快速知道：这个项目在做什么、每个目录负责什么、运行时发生了什么、要改需求时应该让 AI 看哪些文件。

## 1. 项目一句话说明

`LLM_ml` 是一个个人 LLM 工作台：

- 前端提供聊天界面和模型选择。
- 后端管理模型配置、LLM 调用、skill 检索和外部工具。
- 当前重点能力是：当用户输入“搜索、检索、联网、官网、个人主页”等问题时，后端自动触发网页检索 skill，用 DuckDuckGo 获取信息，再把检索结果交给模型生成回答。

## 2. 当前项目结构

```text
.
├─ README.md                         # 快速启动、配置和测试说明
├─ PROJECT_GUIDE.md                  # 当前这份项目导览文档
├─ .env.example                      # 环境变量模板，不含真实密钥
├─ backend/
│  ├─ requirements.txt               # Python 依赖
│  ├─ app/
│  │  ├─ main.py                     # FastAPI 应用入口
│  │  ├─ api/routes.py               # 后端 HTTP API 路由
│  │  ├─ core/config.py              # 全局配置，固定读取仓库根目录 .env
│  │  ├─ config/
│  │  │  ├─ models.example.json      # 可提交的模型配置样例
│  │  │  └─ models.local.example.json
│  │  ├─ models/                     # Pydantic 数据结构
│  │  │  ├─ chat.py                  # 聊天请求、响应、tool call 结构
│  │  │  ├─ llm.py                   # 模型配置结构
│  │  │  ├─ skills.py                # skill 列表和搜索结构
│  │  │  └─ tools.py                 # web search 工具请求/响应结构
│  │  └─ services/
│  │     ├─ chat_orchestrator.py     # 聊天主流程：触发 skill、检索、调用模型、记录日志
│  │     ├─ search_logging.py        # 检索日志，记录 raw output 和 think 内容
│  │     ├─ llm/
│  │     │  ├─ registry.py           # 模型注册表，按 model_id 找 provider
│  │     │  ├─ demo.py               # 本地演示回显模型
│  │     │  └─ openai_compatible.py  # OpenAI-compatible 真实模型适配器
│  │     ├─ skills/
│  │     │  ├─ registry.py           # 读取 skill、判断是否触发检索
│  │     │  └─ search.py             # skill 搜索接口逻辑
│  │     └─ tools/
│  │        ├─ registry.py           # tool schema 和 tool 执行入口
│  │        └─ web_search.py         # DuckDuckGo 检索实现
│  └─ tests/
│     └─ test_api.py                 # 后端 API、检索和日志测试
├─ skills/
│  └─ web-research-homepages/
│     ├─ SKILL.md                    # 联网检索 skill 规则说明
│     └─ agents/openai.yaml          # skill agent 元数据
└─ web/
   ├─ package.json                   # 前端依赖和脚本
   ├─ app/
   │  ├─ page.tsx                    # Next.js 主聊天页面
   │  ├─ layout.tsx                  # 页面 metadata 和根布局
   │  └─ styles.css                  # 前端样式
   └─ static/index.html              # 受限环境下的轻量测试前端
```

## 3. 运行方式

### 后端

推荐从仓库根目录启动：

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\activate
pip install -r backend\requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

也可以在 `backend/` 目录中启动：

```powershell
cd backend
.\.venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

后端的 `config.py` 已固定读取仓库根目录 `.env`，所以不会再因为从 `backend/` 启动而只加载 `demo-local`。

### 前端

```powershell
cd web
npm install
npm run dev
```

打开：

```text
http://localhost:3000
```

如果 Next.js 在某些受限环境里报 `spawn EPERM`，可以先用 `web/static/index.html` 作为临时前端测试页面。

### 后端测试

```powershell
pytest backend\tests
```

当前测试规模：8 个用例。

## 4. 配置文件怎么理解

### `.env`

`.env` 放真实密钥和本地配置，不提交。

关键变量：

```text
LLM_CONFIG_PATH=backend/app/config/models.local.json
DEFAULT_MODEL_ID=DeepSeek-R1-Distill-Qwen-7B
GITEE_AI_TOKEN=你的 token
GITEE_AI_BASE_URL=https://ai.gitee.com/v1
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

### `models.example.json` / `models.local.json`

模型配置长这样：

```json
{
  "provider": "openai-compatible",
  "model_id": "DeepSeek-R1-Distill-Qwen-7B",
  "label": "Gitee DeepSeek R1 Distill Qwen 7B",
  "base_url": "https://ai.gitee.com/v1",
  "api_key_env": "GITEE_AI_TOKEN",
  "tools": false,
  "enabled": true
}
```

含义：

- `provider`: 用哪个模型适配器，目前有 `demo` 和 `openai-compatible`。
- `model_id`: 真正发给模型服务的模型名。
- `label`: 前端下拉框显示名。
- `base_url`: OpenAI-compatible API 地址。
- `api_key_env`: 从哪个环境变量读 token。
- `tools`: 是否把工具 schema 发给模型。
- `enabled`: 是否出现在可用模型列表里。

## 5. 一次聊天请求发生了什么

核心文件：`backend/app/services/chat_orchestrator.py`

流程如下：

```text
前端提交消息
  ↓
POST /api/chat
  ↓
run_chat()
  ↓
判断是否触发 web-research-homepages skill
  ↓
如果触发：search_web() 先检索 DuckDuckGo
  ↓
把检索结果作为内部上下文喂给模型
  ↓
llm_registry 根据 model_id 找 provider
  ↓
OpenAICompatibleProvider 调用真实模型
  ↓
清理 <think> 块，只把干净回答返回前端
  ↓
如果触发过检索，追加 logs/search-runs.jsonl 调试记录
```

普通聊天不会写检索日志；只有触发检索 skill 时才会写。

## 6. 检索能力怎么工作

核心文件：

- `skills/web-research-homepages/SKILL.md`
- `backend/app/services/skills/registry.py`
- `backend/app/services/tools/web_search.py`
- `backend/app/services/chat_orchestrator.py`

触发词在 `skills/registry.py` 中，包括：

```text
搜索、检索、查找、浏览、核实、验证、研究、联网、主页、官网、个人主页、公司官网
```

检索工具默认使用 DuckDuckGo：

1. 先尝试 DuckDuckGo HTML 搜索页。
2. 如果遇到验证码或不可解析结果，回退到 DuckDuckGo Instant Answer API。
3. 对人物/企业类问题，优先官方主页。
4. 如果没有官方主页，百科结果也可接受，例如 Wikipedia、百度百科、Britannica。

检索结果会转成内部上下文，模型不会直接看到“工具怎么调用”的细节，但会看到结果摘要和推荐候选。

## 7. 检索日志在哪里

文件：

```text
logs/search-runs.jsonl
```

每次触发检索 skill 后追加一行 JSON。

记录内容包括：

- `timestamp`: 时间。
- `user_text`: 用户原始问题。
- `search`: 检索请求、结果和 note。
- `recommended_homepage`: 推荐候选，可能是官方主页或百科页。
- `model_outputs`: 模型每轮原始输出。
- `raw_output`: 模型原始内容，包括 `<think>`。
- `thinking`: 从 `<think>...</think>` 提取出的思考内容。
- `tool_calls`: 模型 tool call 记录。
- `final_content`: 清理掉 `<think>` 后返回给前端的内容。

这个日志目录在 `.gitignore` 里，不会提交，适合本地调试。

## 8. 前端怎么工作

核心文件：

- `web/app/page.tsx`
- `web/app/styles.css`

前端启动后做两件事：

1. 请求 `GET /api/models`，填充模型下拉框。
2. 提交聊天时请求 `POST /api/chat`。

前端没有复杂状态管理，主要状态只有：

- `models`: 可用模型列表。
- `modelId`: 当前选择模型。
- `messages`: 聊天消息。
- `input`: 输入框文本。
- `isSending`: 是否正在请求后端。

如果你要让 AI 修改前端，大多数情况只需要让它看：

```text
web/app/page.tsx
web/app/styles.css
backend/app/api/routes.py
backend/app/models/chat.py
```

## 9. 后端接口清单

### 健康检查

```http
GET /api/health
```

返回：

```json
{"status": "ok"}
```

### 模型列表

```http
GET /api/models
```

用于前端模型下拉框。

### 聊天

```http
POST /api/chat
```

请求示例：

```json
{
  "model_id": "DeepSeek-R1-Distill-Qwen-7B",
  "messages": [
    {"role": "user", "content": "检索科比，并返回他的个人主页"}
  ]
}
```

### skill 搜索

```http
POST /api/skills/search
```

### 直接网页检索

```http
POST /api/tools/search-web
```

请求示例：

```json
{"query": "检索科比", "limit": 5}
```

## 10. 常见修改任务应该看哪里

### 想新增一个模型

看：

```text
backend/app/config/models.example.json
backend/app/config/models.local.example.json
backend/app/services/llm/registry.py
backend/app/services/llm/openai_compatible.py
```

通常只需要改本地 `models.local.json`，不需要写代码。

### 想接一个新的模型供应商

看：

```text
backend/app/services/llm/base.py
backend/app/services/llm/openai_compatible.py
backend/app/services/llm/registry.py
```

做法：

1. 新增一个 provider 文件。
2. 继承 `LLMProvider`。
3. 在 `registry.py` 里注册。

### 想改检索触发词

看：

```text
backend/app/services/skills/registry.py
```

### 想改检索排序、百科是否接受、官方主页优先级

看：

```text
backend/app/services/tools/web_search.py
backend/app/services/chat_orchestrator.py
skills/web-research-homepages/SKILL.md
```

### 想记录更多调试信息

看：

```text
backend/app/services/search_logging.py
backend/app/services/chat_orchestrator.py
```

### 想把模型思考过程展示在前端

现在后端只记录 `<think>` 到日志，不返回前端。

如果要展示，需要改：

```text
backend/app/models/chat.py
backend/app/services/chat_orchestrator.py
web/app/page.tsx
```

建议默认不要展示给普通用户，只做开发开关。

### 想改页面布局或按钮

看：

```text
web/app/page.tsx
web/app/styles.css
```

## 11. 给 AI 的推荐提示词

以后你可以直接对 AI 说：

```text
请先阅读 PROJECT_GUIDE.md，然后根据我的需求修改代码。修改前先指出你准备看的文件，修改后运行 pytest backend\tests。
```

如果是检索相关需求，可以说：

```text
请重点阅读 backend/app/services/chat_orchestrator.py、backend/app/services/tools/web_search.py、backend/app/services/search_logging.py 和 skills/web-research-homepages/SKILL.md。
```

如果是前端相关需求，可以说：

```text
请重点阅读 web/app/page.tsx 和 web/app/styles.css。不要改后端，除非接口字段不够用。
```

## 12. 当前已知坑

- 端口 8000 或 3000 可能被旧进程占用。先停旧进程再启动。
- Next.js 在受限环境里可能报 `spawn EPERM`。普通终端运行通常更稳。
- `.env` 和 `backend/app/config/models.local.json` 是本地私有配置，不要提交。
- DuckDuckGo HTML 搜索可能出现验证码页；代码已回退到 Instant Answer API，但不是所有查询都有结构化结果。
- 模型原始输出可能包含 `<think>`。前端默认不展示，日志会记录。

## 13. 最小验收清单

每次改完后，至少做：

```powershell
pytest backend\tests
```

如果改了真实模型或检索链路，再测：

```powershell
python - <<'PY'
import requests

r = requests.post(
    "http://127.0.0.1:8000/api/tools/search-web",
    json={"query": "检索科比", "limit": 5},
    timeout=120,
)
print(r.status_code)
print(r.text[:1000])
PY
```

以及：

```powershell
python - <<'PY'
import requests

r = requests.post(
    "http://127.0.0.1:8000/api/chat",
    json={
        "model_id": "DeepSeek-R1-Distill-Qwen-7B",
        "messages": [{"role": "user", "content": "检索科比，并返回他的个人主页"}],
        "max_tokens": 1024,
    },
    timeout=180,
)
print(r.status_code)
print(r.text[:2000])
PY
```

如果后端实际跑在 8001，把 URL 里的端口替换成 8001。
