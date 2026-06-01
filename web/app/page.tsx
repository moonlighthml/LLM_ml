"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { Bot, Send, Sparkles } from "lucide-react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type ModelInfo = {
  provider: string;
  model_id: string;
  label: string;
};

type ChatResponse = {
  model_id: string;
  content: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [modelId, setModelId] = useState("demo-local");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "你好，我是你的个人 LLM 工作台。你可以输入需要检索或对话的问题。",
    },
  ]);
  const [input, setInput] = useState("搜索科比的个人主页");
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
  }, []);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isSending) return;

    const nextMessages: ChatMessage[] = [...messages, { role: "user", content: trimmed }];
    setMessages([...nextMessages, { role: "assistant", content: `正在调用模型 ${modelId}...` }]);
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
      const data = (await response.json()) as ChatResponse;
      setMessages([...nextMessages, { role: "assistant", content: data.content || "没有返回内容。" }]);
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

      <section className="workspace single">
        <div className="chatPanel">
          <div className="panelHeader">
            <div>
              <p className="eyebrow">对话</p>
              <h2>模型对话</h2>
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
      </section>
    </main>
  );
}
