# LLM_ml

个人 LLM 工作台，用于模型对话、skill 检索和工具式网页检索。

如果你主要通过 vibe coding 让 AI 继续生成和修改代码，建议先阅读 [PROJECT_GUIDE.md](PROJECT_GUIDE.md)。它按“要改什么功能该看哪些文件”的方式整理了项目结构、运行链路和常见坑。

## 技术栈

- `backend/`: Python FastAPI 后端，负责模型供应商、skill 检索和工具接口。
- `web/`: Next.js + React 前端工作台。
- `skills/`: 可公开提交的 skill 示例文件。
- `docs/`: 本地开发说明和工作记录，已被 Git 忽略。

## 快速启动

后端推荐从仓库根目录启动，这样最不容易混淆 `.env`、模型配置和导入路径：

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\activate
pip install -r backend\requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

如果已经在 `backend/` 目录里激活虚拟环境，也可以启动：

```powershell
cd backend
.\.venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

后端现在会固定读取仓库根目录 `.env`，不会再因为当前工作目录不同而只加载 `demo-local`。

前端：

```powershell
cd web
npm install
npm run dev
```

打开 `http://localhost:3000`。

## 配置说明

复制 `.env.example` 为 `.env`，并在本地填写模型供应商密钥。不要提交 `.env`。

常用配置：

- `LLM_CONFIG_PATH`: 模型配置文件路径，真实本地配置可指向 `backend/app/config/models.local.json`。
- `DEFAULT_MODEL_ID`: 默认模型 ID。
- `GITEE_AI_TOKEN`: Gitee 模力方舟 token，用于 OpenAI-compatible LLM 调用。
- `GITEE_AI_BASE_URL`: Gitee OpenAI-compatible base URL，当前为 `https://ai.gitee.com/v1`。
- `NEXT_PUBLIC_API_BASE_URL`: 前端访问的后端地址，默认可用 `http://127.0.0.1:8000`。

公开模板里的 `demo-local` 是本地回显适配器，用来在没有真实 LLM 密钥时验证前后端链路。

## 真实模型

当前本地 `models.local.json` 可启用：

- `DeepSeek-R1-Distill-Qwen-7B`: Gitee 模力方舟 OpenAI-compatible 模型。
- `deepseek-v4-flash`: DeepSeek OpenAI-compatible 模型。
- `demo-local`: 本地演示模型。

真实模型调用已经通过后端 `/api/chat` 验证：

```text
请求：请用一句话回复：真实模型测试成功
返回：测试成功！模型运行正常。
```

## 联网检索 Skill

`web-research-homepages` skill 已接入 `search_web` 工具。

检索工具默认使用免费的 DuckDuckGo：

- 优先尝试 DuckDuckGo HTML 搜索结果。
- 当 DuckDuckGo HTML 返回验证码或不可解析页面时，回退到 DuckDuckGo Instant Answer API。
- 对人物或企业检索，会优先提示模型使用官方个人主页、公司网站或权威资料页。
- 如果没有可靠官方主页，百科结果也可以作为可接受来源，例如 Wikipedia、百度百科、Britannica。

每次触发检索 skill 时，后端会追加一条 JSONL 调试记录：

```text
logs/search-runs.jsonl
```

日志包含用户问题、检索结果、推荐候选、模型原始输出、`<think>` 思考内容、工具调用和清理后的最终输出。该目录已被 Git 忽略，只用于本地调试。

已验证查询：

```text
查询：检索科比
工具结果：Kobe Bryant official website -> http://kobebryant.com
真实模型回答：官方主页：kobebryant.com
```

## 后端接口

- `GET /api/health`
- `GET /api/models`
- `POST /api/chat`
- `POST /api/skills/search`
- `POST /api/tools/search-web`

## 测试

后端测试：

```powershell
pytest backend\tests
```

当前结果：`8 passed`。

## 已知注意事项

- 如果 Next.js 在受限环境中启动时报 `spawn EPERM`，需要在普通终端或获得权限的环境里运行 `npm run dev`。
- 如果 8000 或 3000 端口被旧进程占用，请先停止旧进程再启动服务。
- 本地临时文件、日志和私有配置均不应提交。
