"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Bot, LinkIcon, Search, Send, Sparkles } from "lucide-react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ModelInfo = {
  provider: string;
  model_id: string;
  label: string;
};

type SkillResult = {
  name: string;
  description: string;
  tags: string[];
  score: number;
};

type WebResult = {
  title: string;
  url: string;
  snippet: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export default function Home() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelId, setModelId] = useState("demo-local");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "你好，我是你的个人 LLM 工作台。现在可以先用演示模型验证前后端链路。",
    },
  ]);
  const [input, setInput] = useState("");
  const [skillQuery, setSkillQuery] = useState("");
  const [skills, setSkills] = useState<SkillResult[]>([]);
  const [webQuery, setWebQuery] = useState("");
  const [webResults, setWebResults] = useState<WebResult[]>([]);
  const [isSending, setIsSending] = useState(false);

  const apiStatus = useMemo(() => (models.length > 0 ? "后端已连接" : "等待后端连接"), [models]);

  useEffect(() => {
    fetch(`${apiBaseUrl}/api/models`)
      .then((response) => response.json())
      .then((data) => {
        setModels(data.models || []);
        setModelId(data.default_model_id || "demo-local");
      })
      .catch(() => setModels([]));
  }, []);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    setInput("");
    setIsSending(true);

    try {
      const response = await fetch(`${apiBaseUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_id: modelId,
          messages: nextMessages.map((message) => ({ role: message.role, content: message.content })),
        }),
      });
      const data = await response.json();
      setMessages([...nextMessages, { role: "assistant", content: data.content || "没有返回内容。" }]);
    } catch {
      setMessages([...nextMessages, { role: "assistant", content: "后端暂时不可用，请确认 FastAPI 已启动。" }]);
    } finally {
      setIsSending(false);
    }
  }

  async function searchSkills(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const response = await fetch(`${apiBaseUrl}/api/skills/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: skillQuery, limit: 5 }),
    });
    const data = await response.json();
    setSkills(data.results || []);
  }

  async function searchWeb(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const response = await fetch(`${apiBaseUrl}/api/tools/search-web`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: webQuery, limit: 5 }),
    });
    const data = await response.json();
    setWebResults(data.results || []);
  }

  return (
    <main className="shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">LLM_ml</p>
          <h1>个人 LLM 工作台</h1>
        </div>
        <div className="status">
          <Sparkles size={16} />
          <span>{apiStatus}</span>
        </div>
      </section>

      <section className="workspace">
        <div className="chatPanel">
          <div className="panelHeader">
            <div>
              <p className="eyebrow">对话</p>
              <h2>聊天</h2>
            </div>
            <select value={modelId} onChange={(event) => setModelId(event.target.value)} aria-label="选择模型">
              {models.map((model) => (
                <option key={model.model_id} value={model.model_id}>
                  {model.label}
                </option>
              ))}
              {models.length === 0 && <option value="demo-local">本地演示模型</option>}
            </select>
          </div>

          <div className="messages">
            {messages.map((message, index) => (
              <div className={`message ${message.role}`} key={`${message.role}-${index}`}>
                <div className="avatar">{message.role === "assistant" ? <Bot size={16} /> : "你"}</div>
                <p>{message.content}</p>
              </div>
            ))}
          </div>

          <form className="composer" onSubmit={sendMessage}>
            <input
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="输入问题，例如：帮我找某个人的个人主页"
            />
            <button type="submit" disabled={isSending} aria-label="发送">
              <Send size={18} />
            </button>
          </form>
        </div>

        <aside className="sidePanel">
          <div className="toolBlock">
            <div className="panelHeader compact">
              <div>
                <p className="eyebrow">Skill</p>
                <h2>检索</h2>
              </div>
              <Search size={18} />
            </div>
            <form className="toolForm" onSubmit={searchSkills}>
              <input
                value={skillQuery}
                onChange={(event) => setSkillQuery(event.target.value)}
                placeholder="例如：个人主页搜索"
              />
              <button type="submit">检索</button>
            </form>
            <div className="results">
              {skills.map((skill) => (
                <article className="resultItem" key={skill.name}>
                  <strong>{skill.name}</strong>
                  <p>{skill.description}</p>
                  <span>{skill.tags.join(" / ")}</span>
                </article>
              ))}
            </div>
          </div>

          <div className="toolBlock">
            <div className="panelHeader compact">
              <div>
                <p className="eyebrow">工具</p>
                <h2>网页搜索</h2>
              </div>
              <LinkIcon size={18} />
            </div>
            <form className="toolForm" onSubmit={searchWeb}>
              <input
                value={webQuery}
                onChange={(event) => setWebQuery(event.target.value)}
                placeholder="某个人的个人主页"
              />
              <button type="submit">搜索</button>
            </form>
            <div className="results">
              {webResults.map((result) => (
                <article className="resultItem" key={result.url}>
                  <a href={result.url} target="_blank" rel="noreferrer">
                    {result.title}
                  </a>
                  <p>{result.snippet}</p>
                </article>
              ))}
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}
