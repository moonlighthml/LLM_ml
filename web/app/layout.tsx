import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "个人 LLM 工作台",
  description: "用于对话、skill 检索和工具调用的个人 LLM 工作台",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
