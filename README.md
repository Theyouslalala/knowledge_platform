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
- 反思机制：Critic 评估质量，不通过则带反馈回 Researcher 重做
- `max_iterations` 防止无限循环

### RAG 全链路
- 多格式文档解析：PDF、DOCX、TXT、MD（异步 `asyncio.to_thread`）
- 三种分块策略：固定大小、递归、语义
- Hybrid Search：Dense (ChromaDB) + BM25 + Reciprocal Rank Fusion
- Cross-encoder Reranker（异步模型加载和推理）
- Query Expansion 查询扩展（LLM 生成多查询，并行检索）
- Contextual Compression 上下文压缩

### 工具系统
- 插件化工具注册（`BaseTool` → `ToolRegistry`）
- 内置工具：计算器、沙箱代码执行、Web 搜索、RAG 检索
- 自动 LangChain Tool 桥接（`to_langchain_tool()`）
- 沙箱安全：模块级 `BLOCKED_MODULES`/`BLOCKED_NAMES`，受限环境变量

### 记忆系统
- 短期记忆（对话缓冲 deque）
- 长期记忆（ChromaDB 向量存储，语义检索）
- 工作记忆（当前任务上下文）
- `MemoryManager` 统一协调

### 可观测性
- `TokenTracker`：每次 LLM 调用的 token 统计 + 成本估算
- `ExecutionTracer`：Agent 执行每步记录（推理、工具调用、耗时）
- Trace 存储到内存，支持查询和分析
- Dashboard 页面可视化

### 流式文件上传
- 分块流式写入（64KB chunks），大文件不阻塞
- 实时大小检查，超限立即拒绝并清理

## 快速开始

### 1. 创建环境

```bash
conda create -n knowledge_platform python=3.11
conda activate knowledge_platform
pip install -e ".[dev]"
```

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

关键配置项：
- `OPENAI_API_KEY` 或 `DEEPSEEK_API_KEY` — LLM 调用
- `SECRET_KEY` — JWT 签名（默认自动生成随机值）
- `DEMO_MODE=true` — 无需 API Key 的演示模式

### 3. 启动后端

```bash
uvicorn src.knowledge_platform.main:app --reload
```

访问 http://localhost:8000/docs 查看 Swagger API 文档。

### 4. 启动前端

```bash
python -m src.knowledge_platform.frontend.app
```

访问 http://localhost:7860 使用 Gradio 界面。

### 5. 数据库迁移

```bash
alembic upgrade head
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/auth/register` | 注册（返回 JWT） |
| POST | `/api/v1/auth/login` | 登录 |
| POST | `/api/v1/auth/refresh` | 刷新令牌 |
| GET | `/api/v1/users/me` | 当前用户信息 |
| PATCH | `/api/v1/users/me` | 更新用户 |
| CRUD | `/api/v1/projects` | 项目管理（分页） |
| CRUD | `/api/v1/tasks` | 任务管理 |
| POST | `/api/v1/tasks/{id}/execute` | 执行任务（后台 Agent） |
| POST | `/api/v1/projects/{id}/documents` | 上传文档（流式） |
| GET | `/api/v1/conversations` | 对话列表 |
| GET | `/api/v1/conversations/{id}/messages` | 对话消息（分页） |
| GET | `/api/v1/traces/{task_id}` | 执行 Trace |
| GET | `/api/v1/traces/tokens/summary` | Token 用量汇总 |
| GET | `/api/v1/export/tasks/json` | 导出 JSON |
| GET | `/api/v1/export/tasks/csv` | 导出 CSV |
| GET | `/api/v1/search/messages` | 语义搜索消息 |
| GET | `/health` | 健康检查 |

## 项目结构

```
src/knowledge_platform/
├── main.py                  # FastAPI 应用工厂 + lifespan
├── config.py                # Pydantic Settings（.env 驱动）
├── models/                  # SQLAlchemy 2.0 ORM（9 个模型）
│   ├── base.py              # BaseModel（UUID PK, timestamps）
│   ├── user.py, project.py, task.py
│   ├── conversation.py, message.py
│   ├── document.py, agent_execution.py, tool.py
├── schemas/                 # Pydantic 请求/响应 Schema
│   ├── auth.py              # 注册/登录（Field 约束验证）
│   ├── common.py            # PaginatedResponse 泛型
├── api/                     # FastAPI 路由（RESTful）
│   ├── deps.py              # DI：DatabaseSession, CurrentUser
│   ├── auth.py, users.py, projects.py, tasks.py
│   ├── documents.py         # 流式上传 + 后台 RAG 处理
│   ├── conversations.py, traces.py
│   ├── data_export.py, conversation_search.py
│   ├── router.py            # 路由聚合
│   ├── utils.py             # get_user_resource 等工具
├── core/
│   ├── agents/              # 多 Agent 系统
│   │   ├── base.py          # BaseAgent + _run_tools（并行）
│   │   ├── orchestrator.py  # LangGraph StateGraph 编排
│   │   ├── planner.py, researcher.py, analyst.py
│   │   ├── writer.py, critic.py
│   │   ├── llm_provider.py  # LLM 实例管理（full/mini 双 tier）
│   │   ├── prompts.py       # System Prompt 模板
│   │   ├── state.py         # AgentState TypedDict
│   ├── rag/                 # RAG Pipeline
│   │   ├── document_processor.py  # 多格式解析（async）
│   │   ├── chunker.py       # 分块策略
│   │   ├── embedder.py      # Embedding（OpenAI / 本地）
│   │   ├── vector_store.py  # ChromaDB
│   │   ├── retriever.py     # Hybrid Search（Dense + BM25 + RRF）
│   │   ├── reranker.py      # Cross-encoder（async 加载+推理）
│   │   ├── pipeline.py      # RAGPipeline 编排（并行检索）
│   ├── memory/              # 记忆系统
│   │   ├── short_term.py, long_term.py, working.py
│   │   ├── manager.py       # MemoryManager 统一入口
│   │   ├── base.py          # MemoryEntry
│   ├── tools/               # 工具系统
│   │   ├── base.py          # BaseTool ABC + __init_subclass__
│   │   ├── registry.py      # ToolRegistry 单例
│   │   ├── calculator.py    # 安全表达式求值
│   │   ├── code_executor.py # 沙箱执行（async subprocess）
│   │   ├── web_search.py, rag_tool.py
│   ├── collaboration/       # Agent 协作
│   │   ├── message_bus.py, reflection.py, consensus.py
│   ├── token_tracker.py     # Token 用量统计
│   ├── execution_tracer.py  # 执行 Trace
├── infrastructure/
│   ├── database.py          # Async SQLAlchemy + aiosqlite
│   ├── security.py          # JWT + bcrypt
│   ├── exceptions.py        # AppError 层级
│   ├── health.py            # 健康检查端点
│   ├── logging.py           # 日志配置
├── frontend/
│   ├── app.py               # Gradio 5 页面 UI
tests/
├── conftest.py              # 共享 fixtures（client, auth_headers）
├── unit/                    # 单元测试
│   ├── test_tools.py, test_agents.py, test_chunker.py
│   ├── test_memory.py, test_token_tracker.py
│   ├── test_execution_tracer.py, test_code_executor_sandbox.py
├── integration/             # 集成测试
│   ├── test_api_auth.py, test_api_projects.py, test_api_tasks.py
├── e2e/                     # 端到端测试
```

## 学习资源

- [架构详解](docs/architecture.md) — 系统设计决策和技术细节
- [学习路线](docs/learning_guide.md) — 按阶段学习所有技术点
- [API 文档](docs/api_reference.md) — REST API 完整参考

## License

MIT
