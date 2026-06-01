import type { Metadata } from "next";
import "./styles.css";

export const metadata: Metadata = {
  title: "LLM Workbench",
  description: "Personal LLM workbench for chat, skills, and tools",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

