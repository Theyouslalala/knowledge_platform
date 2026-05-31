# Knowledge Platform

知识增强的多智能体协作平台 — 一个展示 Agent、RAG、后端工程深度的完整 LLM 应用。

## 架构概览

```
用户请求
   │
   ▼
┌──────────────┐
│  Planner     │  任务拆解 Agent
│  Agent       │  分析需求 → 拆分子任务 → 分配
└──────┬───────┘
       │
       ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Research    │  │  Analysis    │  │  Writer      │
│  Agent       │  │  Agent       │  │  Agent       │
│  + RAG检索   │  │  + 数据分析  │  │  + 内容生成  │
│  + Web搜索   │  │  + 代码执行  │  │  + 格式化    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       ▼                 ▼                 ▼
┌─────────────────────────────────────────────────┐
│  Critic Agent                                    │
│  质量审查 → 通过则输出 → 不通过则返回重做         │
└─────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | FastAPI + SQLAlchemy 2.0 (async) + SQLite |
| **LLM** | LangChain + LangGraph + PyTorch |
| **RAG** | ChromaDB + BM25 + Cross-encoder Reranker |
| **前端** | Gradio |
| **认证** | JWT + bcrypt |

## 核心特性

### Multi-Agent 协作
- 5 个专业 Agent：Planner、Researcher、Analyst、Writer、Critic
- LangGraph StateGraph 编排，支持条件边和反思循环
- 反思机制：Critic 评估质量，不通过则回 Researcher 重做

### RAG 全链路
- 三种分块策略：固定大小、递归、语义
- Hybrid Search：Dense (向量) + BM25 (关键词) + RRF 融合
- Cross-encoder Reranker 重排
- Query Expansion 查询扩展
- Contextual Compression 上下文压缩

### 工具系统
- 插件化工具注册
- 内置工具：计算器、代码执行、文件操作、Web 搜索、RAG 检索

### 记忆系统
- 短期记忆（对话缓冲）
- 长期记忆（向量存储）
- 工作记忆（任务上下文）

### Token 追踪
- 每次 LLM 调用的 token 统计
- 成本估算（基于模型定价）
- 执行 Trace 可视化

## 快速开始

### 1. 创建环境

```bash
conda create -n knowledge_platform python=3.11
conda activate knowledge_platform
pip install -e .
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

### 3. 启动后端

```bash
uvicorn src.knowledge_platform.main:app --reload
```

访问 http://localhost:8000/docs 查看 API 文档。

### 4. 启动前端

```bash
python -m src.knowledge_platform.frontend.app
```

访问 http://localhost:7860 使用 Gradio 界面。

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/login` | 登录 |
| GET | `/api/v1/users/me` | 当前用户 |
| CRUD | `/api/v1/projects` | 项目管理 |
| CRUD | `/api/v1/tasks` | 任务管理 |
| POST | `/api/v1/tasks/{id}/execute` | 执行任务 |
| POST | `/api/v1/projects/{id}/documents` | 上传文档 |
| GET | `/api/v1/export/tasks/json` | 导出任务 |
| GET | `/api/v1/search/messages` | 搜索消息 |
| GET | `/health` | 健康检查 |

## 项目结构

```
src/knowledge_platform/
├── main.py              # FastAPI 应用入口
├── config.py            # 配置管理
├── models/              # SQLAlchemy ORM 模型
├── schemas/             # Pydantic 请求/响应模型
├── api/                 # API 路由处理器
├── core/
│   ├── agents/          # 多 Agent 系统
│   ├── rag/             # RAG Pipeline
│   ├── memory/          # 记忆系统
│   ├── tools/           # 工具系统
│   └── collaboration/   # Agent 协作
├── infrastructure/      # 基础设施
├── tasks/               # 后台任务
└── frontend/            # Gradio 前端
```

## 学习资源

- [架构详解](docs/architecture.md)
- [学习路线](docs/learning_guide.md)
- [API 文档](docs/api_reference.md)

## License

MIT
