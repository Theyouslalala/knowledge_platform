# 架构详解

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    Gradio Frontend                    │
│  Chat │ Documents │ Tasks │ Dashboard │ Demo          │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP
┌─────────────────────┴───────────────────────────────┐
│                  FastAPI Backend                      │
│  Auth │ Projects │ Tasks │ Documents │ Traces │ Export│
│  ─── DI: DatabaseSession, CurrentUser (deps.py) ───  │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│              Core Business Logic                      │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐│
│  │ Agents  │  │   RAG   │  │ Memory  │  │  Tools  ││
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘│
│       │            │            │            │       │
│  ┌────┴────────────┴────────────┴────────────┴────┐ │
│  │          LangGraph Orchestrator                 │ │
│  │  Planner → Researcher → Analyst → Writer → Critic│ │
│  │          ↑                           │           │ │
│  │          └──── FAIL (with feedback) ─┘           │ │
│  │                     │ PASS → END                 │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│               Infrastructure                         │
│  SQLite (async) │ ChromaDB │ JWT+bcrypt │ Logging    │
└─────────────────────────────────────────────────────┘
```

## 分层架构

### API 层 (`api/`)
- RESTful 路由，每个资源一个文件
- `deps.py` 定义 DI 类型别名：`DatabaseSession = Annotated[AsyncSession, Depends(get_db)]`
- `CurrentUser` 从 JWT 中解析用户
- `utils.py` 提供 `get_user_resource()` 统一资源权限校验

### Core 层 (`core/`)
- **agents/**: LangGraph StateGraph 编排 5 个 Agent
- **rag/**: 文档处理 → 分块 → 嵌入 → 检索 → 重排 → 压缩
- **memory/**: 短期/长期/工作三层记忆
- **tools/**: 插件化工具注册 + LangChain 桥接
- **collaboration/**: MessageBus、ReflectionEngine、Consensus

### Infrastructure 层 (`infrastructure/`)
- `database.py`: Async SQLAlchemy + aiosqlite，`get_db()` 使用 `session.begin()` 自动事务管理
- `security.py`: JWT 创建/验证 + bcrypt 密码哈希
- `exceptions.py`: `AppError` 基类 → 类型化子类，全局异常处理器返回 `{"error": code, "message": msg}`

### Models 层 (`models/`)
- 所有模型继承 `BaseModel`（UUID 字符串主键，`created_at`/`updated_at`）
- `updated_at` 通过 SQLAlchemy `event.listens_for(BaseModel, "before_update")` 自动更新
- 关系使用 `lazy="raise"`（异步安全，防止隐式加载）

## 关键设计决策

### 1. LangGraph 编排

选择 LangGraph 而非手写 asyncio 的原因：
- 声明式图定义，拓扑一目了然
- 内置条件边支持反思循环
- `AgentState`（TypedDict）是共享状态，`messages` 使用 `operator.add` reducer
- 支持检查点和恢复（可扩展）

`AgentOrchestrator._build_graph()` 构建图：
```python
for name in self.agents:
    workflow.add_node(name, self._make_runner(name))
# 条件边：Critic 评估 → approve 到 END / revise 回 Researcher
workflow.add_conditional_edges("critic", self._route_after_critique, {...})
```

### 2. Agent 双 Tier LLM

- `"full"` tier（gpt-4o）：Planner、Critic — 需要深度推理
- `"mini"` tier（gpt-4o-mini）：Researcher、Analyst、Writer — 执行层

`LLMProvider` 按 tier 缓存实例，`get_llm("mini")` / `get_llm("full")` 获取。

### 3. Hybrid Search 三阶段检索

```
Query → QueryExpander（LLM 生成多查询）
     → 并行检索（Dense + BM25，asyncio.gather）
     → Reciprocal Rank Fusion 融合
     → Cross-encoder Reranker（async 模型加载 + 推理）
     → Contextual Compression（LLM 提取关键段落）
```

- Dense：ChromaDB 向量搜索（语义相似度）
- BM25：关键词匹配（精确匹配）
- RRF：`score = Σ 1/(k + rank_i)` 融合多路排名
- Reranker：Cross-encoder 精排，模型加载和推理均在 `asyncio.to_thread`

### 4. 反思循环

```
Planner → Researcher → Analyst → Writer → Critic
                ↑                              │
                └──── FAIL (with feedback) ─────┘
                                    │
                                  PASS → END
```

- `max_iterations`（默认 3）防止无限循环
- Critic 输出结构化评估，失败时带反馈回到 Researcher
- `_route_after_critique()` 检查 `status == "completed"` 或达到最大迭代

### 5. 工具系统

插件化设计：
- `BaseTool` ABC：`name`、`description`、`parameters_schema`、`execute()`
- `__init_subclass__` 自动拷贝 `parameters_schema`（避免可变默认值共享）
- `ToolRegistry` 类级单例：`register()`、`get()`、`get_all()`
- `to_langchain_tool()` 动态创建 Pydantic 模型桥接 LangChain
- `BaseAgent._run_tools()` 并行执行工具（`asyncio.gather`），自动根据 `parameters_schema` 映射参数名

沙箱安全（CodeExecutor）：
- `BLOCKED_MODULES`：禁止导入 os、subprocess、sys 等
- `BLOCKED_NAMES`：覆盖 open、exec、eval、__import__ 等内置函数
- `GUARD_PREAMBLE`：在子进程代码前注入安全守卫
- `asyncio.create_subprocess_exec`：异步执行，不阻塞事件循环
- 受限 `env`：仅传递 PATH（Python 目录）、TEMP、TMP

### 6. 记忆系统

三层架构：
- **短期记忆**（`ShortTermMemory`）：deque 缓冲最近 N 条对话
- **长期记忆**（`LongTermMemory`）：ChromaDB 向量存储，语义检索历史对话
- **工作记忆**（`WorkingMemory`）：当前任务上下文（字典）

`MemoryManager.get_context()` 组装三层记忆上下文，注入 Agent 状态。

### 7. 事务管理

`get_db()` 使用 `session.begin()` 上下文管理器：
```python
async def get_db() -> AsyncSession:
    async with async_session_factory() as session:
        async with session.begin():
            yield session
```
- 成功退出自动 commit
- 异常自动 rollback
- 无需手动 `session.commit()` / `session.rollback()`

### 8. 可观测性

**TokenTracker**：
- `record()` 记录每次 LLM 调用的 token 用量
- `get_task_summary()` 按任务汇总
- `get_total_summary()` 全局汇总
- 自动淘汰旧记录（`MAX_RECORDS`/`MAX_TASKS`）

**ExecutionTracer**：
- `start_trace()` / `agent_start()` / `agent_end()` / `error()` 记录执行流程
- `get_summary()` 返回结构化 trace 数据
- 按插入顺序淘汰旧任务（非 UUID 排序）

## 数据库模型关系

```
User ──1:N── Project ──1:N── Task
                │                │
                ├──1:N── Document │
                │                │
                └──1:N── Conversation ──1:N── Message
                                           │
Task ──1:N── AgentExecution               │
                                           │
TokenUsage ──(task_id)────────────────────┘
```

所有外键使用 UUID 字符串，关系设置 `lazy="raise"`（异步安全）。

## 配置管理

`config.py` 使用 `pydantic-settings`：
- 从 `.env` 文件加载
- `@lru_cache` 单例
- 支持 OpenAI 和 DeepSeek（兼容 API）
- `demo_mode` 开关：无需 API Key 的受限模式
