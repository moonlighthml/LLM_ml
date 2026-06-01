# LLM_ml

个人 LLM 工作台，用于对话、skill 检索和工具式网页搜索。

## 技术栈

- `backend/`：Python FastAPI 后端，负责模型供应商、skill 检索和工具接口。
- `web/`：Next.js + React 前端工作台。
- `skills/`：可公开提交的 skill 样例文件。
- `docs/`：仅本地使用的项目说明，已被 Git 忽略。

## 快速启动

后端：

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd web
npm install
npm run dev
```

打开 `http://localhost:3000`。

## 配置说明

复制 `.env.example` 为 `.env`，并在本地填写模型供应商密钥。不要提交 `.env`。

默认模型定义位于 `backend/app/config/models.example.json`。新增模型时优先增加模型配置；如果接口格式不同，再在 `backend/app/services/llm/` 下新增供应商适配器。

本地付费 API 测试时，密钥只放在 `.env`；也可以把 `LLM_CONFIG_PATH` 指向已被忽略的 `backend/app/config/models.local.json`。

当前已预留的 OpenAI 兼容接口：

- DeepSeek: `https://api.deepseek.com`
- Gitee 模力方舟：`https://ai.gitee.com/v1`；当前本地默认模型是 `DeepSeek-R1-Distill-Qwen-7B`。

## 后端接口

- `GET /api/health`
- `GET /api/models`
- `POST /api/chat`
- `POST /api/skills/search`
- `POST /api/tools/search-web`

公开模板里的默认模型 `demo-local` 是本地回显适配器，用来在没有真实 LLM 密钥时验证前后端链路。
