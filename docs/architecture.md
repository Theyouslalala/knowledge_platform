# 架构详解

## 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                     前端层 (frontend/)                        │
│              Gradio 5 页面 UI (app.py)                        │
│         Chat │ Documents │ Tasks │ Dashboard │ Demo           │
└───────────────────────────────┬─────────────────────────────┘
                                │ HTTP
┌───────────────────────────────┴─────────────────────────────┐
│                      API 层 (api/)                            │
│           FastAPI RESTful 路由 + 依赖注入                      │
│                                                               │
│  auth.py     用户认证（注册/登录/刷新Token）                    │
│  users.py    用户信息管理                                      │
│  projects.py 项目 CRUD（分页）                                 │
│  tasks.py    任务 CRUD + 后台执行                              │
│  documents.py 文档上传（流式）+ 后台 RAG 处理                   │
│  conversations.py 对话管理                                     │
│  traces.py   执行 Trace + Token 统计查询                       │
│  data_export.py JSON/CSV 导出                                  │
│  conversation_search.py 语义搜索                               │
│  deps.py     DI 类型别名 (DatabaseSession, CurrentUser)        │
│  utils.py    共享工具 (get_user_resource)                      │
│  router.py   路由聚合注册                                      │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────┐
│                     Core 层 (core/)                           │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   agents/    │  │     rag/    │  │   memory/   │          │
│  │             │  │             │  │             │          │
│  │ LangGraph   │  │ 文档→分块→  │  │ 短期/长期/  │          │
│  │ 5 Agent     │  │ 嵌入→检索→  │  │ 工作记忆    │          │
│  │ 反思循环    │  │ 重排→压缩   │  │ Manager     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   tools/    │  │ token_tracker│  │ execution_  │          │
│  │             │  │             │  │   tracer    │          │
│  │ BaseTool    │  │ Token 统计  │  │ 执行记录    │          │
│  │ Registry    │  │ 成本估算    │  │ Trace 查询  │          │
│  │ 4 内置工具  │  │             │  │             │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                               │
│  ┌─────────────────────────────────────────────┐             │
│  │            collaboration/                     │             │
│  │   MessageBus │ ReflectionEngine │ Consensus   │             │
│  └─────────────────────────────────────────────┘             │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────┐
│                  基础设施层 (infrastructure/)                   │
│                                                               │
│  database.py    Async SQLAlchemy + aiosqlite                  │
│  security.py    JWT 创建/验证 + bcrypt 密码哈希                │
│  exceptions.py  AppError 异常层级 + 全局处理器                  │
│  health.py      /health 健康检查端点                           │
│  logging.py     日志配置                                      │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────┐
│                     数据层 (models/)                           │
│                                                               │
│  base.py         BaseModel (UUID PK, created_at, updated_at) │
│  user.py         用户模型                                     │
│  project.py      项目模型                                     │
│  task.py         任务模型                                     │
│  conversation.py 对话模型                                     │
│  message.py      消息模型                                     │
│  document.py     文档模型                                     │
│  agent_execution.py Agent 执行记录                             │
│  tool.py         工具配置                                     │
│                                                               │
│  所有模型: lazy="raise" (异步安全)                             │
│  updated_at: event.listens_for 自动更新                        │
└─────────────────────────────────────────────────────────────┘
```

## 分层架构详解

### API 层 (`api/`)
- RESTful 路由，每个资源一个文件
- `deps.py` 定义 DI 类型别名：`DatabaseSession = Annotated[AsyncSession, Depends(get_db)]`
- `CurrentUser` 从 JWT Bearer Token 解析用户
- `utils.py` 提供 `get_user_resource()` 统一资源权限校验
- `router.py` 聚合所有子路由注册到 `api_router`

### Core 层 (`core/`)
- **agents/**: LangGraph StateGraph 编排 5 个 Agent
- **rag/**: 文档处理 → 分块 → 嵌入 → 检索 → 重排 → 压缩
- **memory/**: 短期/长期/工作三层记忆
- **tools/**: 插件化工具注册 + LangChain 桥接
- **collaboration/**: MessageBus、ReflectionEngine、Consensus
- **token_tracker.py**: Token 用量统计 + 成本估算
- **execution_tracer.py**: Agent 执行 Trace 记录

### Infrastructure 层 (`infrastructure/`)
- `database.py`: Async SQLAlchemy + aiosqlite，`get_db()` 使用 `session.begin()` 自动事务管理
- `security.py`: JWT 创建/验证 + bcrypt 密码哈希
- `exceptions.py`: `AppError` 基类 → 类型化子类，全局异常处理器返回 `{"error": code, "message": msg}`

### Models 层 (`models/`)
- 所有模型继承 `BaseModel`（UUID 字符串主键，`created_at`/`updated_at`）
- `updated_at` 通过 SQLAlchemy `event.listens_for(BaseModel, "before_update")` 自动更新
- 关系使用 `lazy="raise"`（异步安全，防止隐式加载）

## Agent 编排流程

```
用户查询
    │
    ▼
┌──────────┐     ┌──────────────┐
│ Planner  │────▶│  Researcher  │◀─────┐
│ (full)   │     │  (mini)      │      │
│ 任务拆解 │     │  RAG + Web   │      │
└──────────┘     └──────┬───────┘      │
                        │              │
                        ▼              │
                ┌──────────────┐       │
                │   Analyst    │       │
                │  (mini)      │       │  FAIL
                │  Calculator  │       │  (with feedback)
                └──────┬───────┘       │
                        │              │
                        ▼              │
                ┌──────────────┐       │
                │   Writer     │       │
                │  (mini)      │       │
                │  内容生成    │       │
                └──────┬───────┘       │
                        │              │
                        ▼              │
                ┌──────────────┐       │
                │   Critic     │───────┘
                │  (full)      │
                │  质量审查    │
                └──────┬───────┘
                        │
                     PASS ▼
                    ┌──────┐
                    │ END  │
                    └──────┘

max_iterations=3 防止无限循环
```

### Agent 角色详解

| Agent | 文件 | LLM Tier | 工具 | 职责 |
|-------|------|----------|------|------|
| Planner | `planner.py` | full | 无 | 分析需求，拆分子任务，制定执行计划 |
| Researcher | `researcher.py` | mini | RAG + Web | 信息检索，收集相关资料 |
| Analyst | `analyst.py` | mini | Calculator | 数据分析，计算验证 |
| Writer | `writer.py` | mini | 无 | 内容生成，格式化输出 |
| Critic | `critic.py` | full | 无 | 质量审查，输出 PASS/FAIL + 反馈 |

### 共享状态 (AgentState)

```python
class AgentState(TypedDict):
    task_id: str                           # 任务 ID
    user_query: str                        # 用户原始查询
    messages: Annotated[list, operator.add] # 消息列表（自动追加）
    current_agent: str                     # 当前执行的 Agent
    plan: str | None                       # Planner 生成的计划
    research_results: list[str]            # Researcher 检索结果
    analysis: str | None                   # Analyst 分析结果
    draft: str | None                      # Writer 生成的草稿
    critique: str | None                   # Critic 评估反馈
    iteration: int                         # 当前迭代次数
    max_iterations: int                    # 最大迭代次数
    status: str                            # planning/executing/reviewing/revising/completed
    final_output: str | None               # 最终输出
    metadata: dict                         # 元数据（含 memory_context）
```

### 编排实现

```python
# orchestrator.py
class AgentOrchestrator:
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        # 注册节点（工厂模式）
        for name in self.agents:
            workflow.add_node(name, self._make_runner(name))

        # 定义边
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "analyst")
        workflow.add_edge("analyst", "writer")
        workflow.add_edge("writer", "critic")

        # 条件边：反思循环
        workflow.add_conditional_edges(
            "critic",
            self._route_after_critique,
            {"approve": END, "revise": "researcher"},
        )

        return workflow.compile()
```

## RAG Pipeline 流程

### 文档处理流程

```
文档上传 (流式 64KB chunks)
    │
    ▼
DocumentProcessor (asyncio.to_thread)
    │ PDF → pypdf 解析
    │ DOCX → python-docx 解析
    │ TXT/MD → 直接读取
    ▼
Chunker (RecursiveChunker)
    │ 按分隔符层级切分
    │ \n\n → \n → 句子 → 字符
    ▼
Embedder (OpenAI / Local)
    │ OpenAI: 异步 API 调用
    │ Local: asyncio.to_thread 包装
    ▼
存储
    ├── ChromaDB (向量存储)
    └── BM25Index (倒排索引)
```

### 检索流程

```
用户查询
    │
    ▼
QueryExpander (LLM 生成多查询)
    │ "什么是RAG" →
    │   "RAG的定义"
    │   "RAG的工作原理"
    │   "RAG的应用场景"
    ▼
并行检索 (asyncio.gather)
    ├── Dense Retrieval (ChromaDB 向量搜索)
    └── BM25 (关键词匹配)
    │
    ▼
Reciprocal Rank Fusion
    │ score = Σ 1/(k + rank_i)
    │ 融合多路排名结果
    ▼
Cross-encoder Reranker (async)
    │ asyncio.to_thread 加载模型
    │ asyncio.to_thread 执行推理
    │ 精排，返回 top_k 结果
    ▼
Contextual Compression (LLM)
    │ 提取关键段落
    │ 压缩无关内容
    ▼
返回 list[RetrievalResult]
```

### 关键实现

```python
# pipeline.py - 并行检索
if use_expansion:
    queries = await self.query_expander.expand(query)
    results_lists = await asyncio.gather(
        *[self.retriever.retrieve(q, top_k=top_k) for q in queries]
    )
    all_results = [r for sublist in results_lists for r in sublist]

# reranker.py - 异步模型加载
async def rerank(self, query, documents, top_k=5):
    if self._model is None:
        await asyncio.to_thread(self._load_model)
    scores = await asyncio.to_thread(self._model.predict, pairs)
```

## 工具系统

### 架构图

```
BaseTool (ABC)
    ├── name: str
    ├── description: str
    ├── parameters_schema: dict
    ├── execute(**kwargs) -> ToolResult
    └── to_langchain_tool() → LangChain Tool
         │
         │  __init_subclass__ 自动拷贝 schema
         │
    ┌────┴────────────────────────────────────────┐
    │              ToolRegistry                    │
    │  register(tool) / get(name) / get_all()      │
    │  get_langchain_tools() → list[LangChain Tool]│
    └─────────────────────────────────────────────┘
         │
    ┌────┴──────┬──────────┬──────────┐
    │Calculator │CodeExec  │WebSearch │RAGRetrieval
    │ AST安全   │ 沙箱     │ 可配置   │ 知识检索
    │ 求值      │ async    │          │
    └───────────┴──────────┴──────────┘
```

### BaseAgent._run_tools() 并行执行

```python
async def _run_tools(self, **kwargs) -> list[str]:
    async def _run_one(tool):
        tool_kwargs = self._resolve_tool_kwargs(tool, kwargs)
        result = await tool.execute(**tool_kwargs)
        status = "OK" if result.success else "FAILED"
        return f"[{tool.name}] {status}: {result.output}"

    results = await asyncio.gather(*[_run_one(t) for t in self.tools])
    return list(results)
```

`_resolve_tool_kwargs()` 根据工具的 `parameters_schema.required[0]` 自动映射参数名。例如传入 `query="..."` 但工具需要 `expression=`，会自动转换。

### 沙箱安全 (CodeExecutor)

```
用户代码
    │
    ▼
Guard Preamble 注入
    │ 覆盖 __import__ → 拦截 BLOCKED_MODULES
    │ 覆盖 open/exec/eval 等 → 设为 None
    ▼
asyncio.create_subprocess_exec
    │ sys.executable + temp_path
    │ env: 仅 PATH (Python 目录), TEMP, TMP
    │ timeout: 10s
    ▼
输出限制: stdout 10KB, stderr 5KB
```

**BLOCKED_MODULES**: os, subprocess, shutil, sys, pathlib, socket, http, urllib, requests, ctypes, importlib, code, codeop, compileall, py_compile

**BLOCKED_NAMES**: open, exec, eval, compile, __import__, globals, locals, vars, dir, getattr, setattr, delattr, breakpoint, exit, quit

## 记忆系统

### 三层架构

```
MemoryManager
    │
    ├── get_context(task_id, query)
    │       │
    │       ├── ShortTermMemory → 最近 N 条对话 (deque)
    │       ├── LongTermMemory  → 语义检索历史 (ChromaDB)
    │       └── WorkingMemory   → 当前任务上下文 (dict)
    │       │
    │       └── 组装为上下文字符串，注入 AgentState.metadata
    │
    └── store_interaction(MemoryEntry)
            │
            ├── ShortTermMemory.add()
            └── LongTermMemory.add()
```

| 类型 | 文件 | 存储 | 用途 |
|------|------|------|------|
| 短期 | `short_term.py` | deque | 最近 N 条对话缓冲 |
| 长期 | `long_term.py` | ChromaDB | 语义检索历史对话 |
| 工作 | `working.py` | dict | 当前任务上下文 |

## 数据库模型关系

```
User ──1:N── Project ──1:N── Task
                │           │
                ├──1:N── Document
                │
                └──1:N── Conversation ──1:N── Message

Task ──1:N── AgentExecution
TokenUsage ──(task_id)
```

所有外键使用 UUID 字符串，关系设置 `lazy="raise"`（异步安全）。

## 请求认证流程

```
客户端请求
    │
    ▼
Authorization: Bearer <token>
    │
    ▼
FastAPI Depends(CurrentUser)
    │
    ▼
security.py: verify_token(token)
    │ JWT 解码 + 过期检查
    ▼
数据库查询 User
    │
    ▼
注入到路由函数 user 参数
```

## 可观测性

### TokenTracker

```python
# 记录每次 LLM 调用
token_tracker.record(
    task_id="task_001",
    agent_name="planner",
    model_name="gpt-4o",
    prompt_tokens=500,
    completion_tokens=200,
)

# 查询汇总
task_summary = token_tracker.get_task_summary("task_001")
# → {"total_tokens": 700, "total_cost": 0.003, "by_agent": {...}}

total_summary = token_tracker.get_total_summary()
# → {"total_tokens": 50000, "total_cost": 0.05, "total_records": 120}
```

### ExecutionTracer

```python
# 记录执行流程
tracer.start_trace("task_001")
tracer.agent_start("task_001", "planner")
tracer.agent_end("task_001", "planner", duration_ms=1500)
tracer.tool_call("task_001", "researcher", "knowledge_retrieval", {"query": "..."})
tracer.tool_result("task_001", "researcher", "knowledge_retrieval", "result...")
tracer.error("task_001", "writer", "timeout")

# 查询
trace = tracer.get_summary("task_001")
# → {"total_events": 6, "tool_calls": 1, "errors": 1, "agents_involved": [...]}
```

## 关键设计决策

### 1. LangGraph vs asyncio 手写编排

| 维度 | LangGraph | asyncio 手写 |
|------|-----------|-------------|
| 可读性 | 声明式图定义 | 命令式嵌套 |
| 条件边 | 内置支持 | 需手动 if/else |
| 状态管理 | TypedDict + reducer | 手动传递 |
| 检查点 | 内置支持 | 需自行实现 |
| 调试 | 图可视化 | 日志追踪 |

选择 LangGraph：声明式、可扩展、内置反思循环支持。

### 2. session.begin() vs 手动 commit/rollback

```python
# 旧写法（容易遗漏 rollback）
try:
    yield session
    await session.commit()
except Exception:
    await session.rollback()
    raise
finally:
    await session.close()

# 新写法（自动管理）
async with session.begin():
    yield session
```

### 3. lazy="raise" vs lazy="selectin"

- `selectin`: 异步环境下会触发隐式 SQL 查询，导致 N+1 问题
- `raise`: 访问未加载的关系时立即报错，强制开发者显式加载

### 4. asyncio.to_thread vs 同步调用

在 async 上下文中调用同步 I/O（文件读写、模型加载、subprocess）会阻塞事件循环。统一使用 `asyncio.to_thread()` 包装。

### 5. 工具参数自动映射

`_resolve_tool_kwargs()` 根据 `parameters_schema.required[0]` 自动将通用参数名映射为工具所需的具体参数名，避免每个 Agent 硬编码工具特定的参数。

## 配置管理

```python
# config.py
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    llm_provider: str = "openai"
    openai_api_key: str = ""
    deepseek_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/knowledge_platform.db"
    secret_key: str = ""  # 自动生成
    cors_origins: list[str] = [...]
    chroma_persist_dir: str = "./data/chroma"
    embedding_provider: str = "openai"
    demo_mode: bool = False

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
```

`@lru_cache` 保证全局单例，`.env` 文件驱动所有配置。
