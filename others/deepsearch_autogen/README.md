## DeepSearch AutoGen 多智能体协作

本模块演示如何用 AutoGen 组织多智能体做“深度检索 + 证据综合（deepsearch）”。

- 目标：
  - 学习 deepsearch 的方法论（分工、循环、批判、综合）。
  - 面试可展示的多智能体协作范式与可吹点。
  - 提供一键运行的 CLI 与可复用代码结构。

### 目录结构

```
others/deepsearch_autogen/
  ├── agents.py          # 定义 Planner / Researcher / Analyst / Critic / Synthesizer
  ├── orchestrator.py    # 编排群聊，驱动 deepsearch 主循环
  ├── search.py          # DuckDuckGo 搜索 + 网页正文抽取
  ├── prompts.py         # 角色 System Prompt
  ├── main.py            # CLI 入口（保存 Markdown 答案和可选的对话记录）
  ├── requirements.txt   # 依赖
  └── README.md          # 使用和原理说明
```

### 快速开始（本地运行）

1) 安装依赖（建议使用虚拟环境）

```bash
pip install -r others/deepsearch_autogen/requirements.txt
pip install -U "autogen-agentchat" "autogen-ext[openai]"
pip install ddgs
```


