"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Bot, LinkIcon, Send, Sparkles, Wrench } from "lucide-react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ModelInfo = {
  provider: string;
  model_id: string;
  label: string;
};

type ConfiguredSkill = {
  name: string;
  description: string;
  tags: string[];
  tool: string;
  triggers: string[];
};

type Reference = {
  title: string;
  url: string;
  snippet: string;
};

type ToolCall = {
  name: string;
  input: Record<string, unknown>;
  output: {
    note?: string;
    results?: Reference[];
  };
};

type ChatResponse = {
  model_id: string;
  content: string;
  tool_calls: ToolCall[];
  references: Reference[];
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelId, setModelId] = useState("demo-local");
  const [skills, setSkills] = useState<ConfiguredSkill[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "你好，我是你的个人 LLM 工作台。你可以输入需要检索或对话的问题。",
    },
  ]);
  const [input, setInput] = useState("搜索科比的个人主页");
  const [toolCalls, setToolCalls] = useState<ToolCall[]>([]);
  const [references, setReferences] = useState<Reference[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [connectionError, setConnectionError] = useState("");

  const apiStatus = useMemo(() => (models.length > 0 ? "后端已连接" : "等待后端连接"), [models]);

  useEffect(() => {
    fetch(`${apiBaseUrl}/api/models`)
      .then((response) => response.json())
      .then((data) => {
        setModels(data.models || []);
        setModelId(data.default_model_id || "demo-local");
        setConnectionError("");
      })
      .catch((error: Error) => {
        setModels([]);
        setConnectionError(`无法连接后端：${error.message}`);
      });

    fetch(`${apiBaseUrl}/api/skills`)
      .then((response) => response.json())
      .then((data) => setSkills(data.skills || []))
      .catch(() => setSkills([]));
  }, []);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: trimmed }];
    setMessages([
      ...nextMessages,
      { role: "assistant", content: `正在判断是否需要调用 skill，并准备调用模型 ${modelId}...` },
    ]);
    setInput("");
    setIsSending(true);
    setToolCalls([]);
    setReferences([]);

    try {
      const response = await fetch(`${apiBaseUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model_id: modelId,
          messages: nextMessages.map((message) => ({ role: message.role, content: message.content })),
        }),
      });
      const data = (await response.json()) as ChatResponse;
      setMessages([...nextMessages, { role: "assistant", content: data.content || "没有返回内容。" }]);
      setToolCalls(data.tool_calls || []);
      setReferences(data.references || []);
    } catch {
      setMessages([...nextMessages, { role: "assistant", content: "后端暂时不可用，请确认 FastAPI 已启动。" }]);
    } finally {
      setIsSending(false);
    }
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
          <span>{connectionError || apiStatus}</span>
        </div>
      </section>

      <section className="workspace">
        <div className="chatPanel">
          <div className="panelHeader">
            <div>
              <p className="eyebrow">对话</p>
              <h2>模型与 Skill 联动</h2>
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
              placeholder="输入你想检索或对话的问题"
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
                <p className="eyebrow">Skills</p>
                <h2>已配置 Skill</h2>
              </div>
              <Wrench size={18} />
            </div>
            <div className="results">
              {skills.map((skill) => (
                <article className="resultItem" key={skill.name}>
                  <strong>{skill.name}</strong>
                  <p>{skill.description}</p>
                  <span>工具：{skill.tool}</span>
                </article>
              ))}
              {skills.length === 0 && <p className="emptyText">暂无已加载的 skill。</p>}
            </div>
          </div>

          <div className="toolBlock">
            <div className="panelHeader compact">
              <div>
                <p className="eyebrow">调用过程</p>
                <h2>本轮工具结果</h2>
              </div>
              <LinkIcon size={18} />
            </div>
            <div className="results">
              {toolCalls.map((call, index) => (
                <article className="resultItem" key={`${call.name}-${index}`}>
                  <strong>{call.name}</strong>
                  <p>{call.output.note || "工具已执行。"}</p>
                </article>
              ))}
              {references.map((reference) => (
                <article className="resultItem" key={reference.url}>
                  <a href={reference.url} target="_blank" rel="noreferrer">
                    {reference.title}
                  </a>
                  <p>{reference.snippet}</p>
                </article>
              ))}
              {toolCalls.length === 0 && references.length === 0 && (
                <p className="emptyText">当对话触发 skill 后，这里会显示工具调用和候选链接。</p>
              )}
            </div>
          </div>
        </aside>
      </section>
    </main>
  );
}
