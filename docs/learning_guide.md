# 学习路线

本项目覆盖以下核心技术点，按学习顺序排列。每个阶段标注了对应源文件，建议边读代码边实践。

## 1. LLM 基础

### Prompt Engineering
- System Prompt 设计（`core/agents/prompts.py`）
- Few-shot 示例引导
- Chain-of-Thought 推理

### LLM API 调用
- OpenAI API / 兼容 API（DeepSeek、通义千问）（`core/agents/llm_provider.py`）
- 双 Tier 模型管理：`"full"` (gpt-4o) 和 `"mini"` (gpt-4o-mini)
- `LLMProvider` 按 tier 缓存实例
- 流式输出支持

### Token 追踪与成本估算
- `TokenTracker`（`core/token_tracker.py`）：记录每次 LLM 调用的 prompt/completion tokens
- 按任务和全局汇总
- 自动淘汰旧记录（`MAX_RECORDS`/`MAX_TASKS` 上限）

## 2. RAG (Retrieval-Augmented Generation)

### 文档处理
- 多格式异步解析：PDF、DOCX、TXT、MD（`core/rag/document_processor.py`）
- `asyncio.to_thread` 包装同步 I/O，避免阻塞事件循环
- 合并读取 + stat 为单次线程调用

### 分块策略
- 固定大小分块（FixedChunker）
- 递归分块（RecursiveChunker）— 按分隔符层级切分
- 语义分块（SemanticChunker）— 基于 Embedding 相似度
- 代码：`core/rag/chunker.py`

### Embedding 模型
- OpenAI Embedding（`OpenAIEmbedder`，异步 API）
- 本地 Sentence-Transformers（`LocalEmbedder`，`asyncio.to_thread` 包装）
- 统一 `BaseEmbedder` 接口：`embed()`、`embed_batch()`、`dimension`
- 代码：`core/rag/embedder.py`

### 向量数据库
- ChromaDB 内嵌运行（`core/rag/vector_store.py`）
- 持久化到 `data/chroma/`

### 高级检索（三阶段 Pipeline）
1. **Query Expansion**：LLM 生成多个搜索查询，并行检索（`asyncio.gather`）
2. **Hybrid Search**：Dense (向量) + BM25 (关键词) + Reciprocal Rank Fusion（`core/rag/retriever.py`）
3. **Cross-encoder Reranker**：精排，模型加载和推理均异步（`core/rag/reranker.py`）
4. **Contextual Compression**：LLM 提取关键段落（`core/rag/pipeline.py`）

### RAG Pipeline 编排
- `RAGPipeline`（`core/rag/pipeline.py`）串联全部阶段
- `ingest()`：文档 → 分块 → 嵌入 → 存储
- `retrieve()`：查询扩展 → 并行检索 → 融合 → 重排 → 压缩

## 3. Agent 系统

### Agent 架构
- `BaseAgent` 抽象（`core/agents/base.py`）
- `_run_tools(**kwargs)`：并行执行工具（`asyncio.gather`），自动参数映射
- `_resolve_tool_kwargs()`：根据工具 `parameters_schema` 自动路由参数名

### 多 Agent 协作
- LangGraph `StateGraph`（`core/agents/orchestrator.py`）
- `AgentState`（TypedDict）共享状态，`messages` 使用 `operator.add` reducer
- `_make_runner()` 工厂注册节点
- 条件边反思循环

### 5 个 Agent 角色
| Agent | 文件 | LLM Tier | 工具 | 职责 |
|-------|------|----------|------|------|
| Planner | `planner.py` | full | 无 | 任务拆解、制定计划 |
| Researcher | `researcher.py` | mini | RAG + Web | 信息检索 |
| Analyst | `analyst.py` | mini | Calculator | 数据分析、计算 |
| Writer | `writer.py` | mini | 无 | 内容生成、格式化 |
| Critic | `critic.py` | full | 无 | 质量审查、评估反馈 |

### 反思循环详解
```
Planner → Researcher → Analyst → Writer → Critic
                ↑                              │
                └──── FAIL (with feedback) ─────┘
                                    │
                                  PASS → END
```
- `_route_after_critique()`：检查 `status == "completed"` 或达到 `max_iterations`
- 失败时 Critic 的反馈注入 Researcher 的下一轮检索

## 4. 工具系统

### 工具设计
- `BaseTool` ABC（`core/tools/base.py`）：`name`、`description`、`parameters_schema`、`execute()`
- `__init_subclass__` 自动拷贝 `parameters_schema`（避免可变默认值共享）
- `to_langchain_tool()` 动态创建 Pydantic 模型桥接 LangChain

### 工具注册表
- `ToolRegistry`（`core/tools/registry.py`）：类级单例
- `register()`、`get()`、`get_all()`、`get_langchain_tools()`
- Orchestrator 启动时自动注册内置工具

### 内置工具
| 工具 | 文件 | 说明 |
|------|------|------|
| Calculator | `calculator.py` | AST 安全表达式求值 |
| CodeExecutor | `code_executor.py` | 沙箱 Python 执行 |
| WebSearch | `web_search.py` | Web 搜索（可配置） |
| RAGRetrieval | `rag_tool.py` | RAG 知识检索 |

### 沙箱安全（CodeExecutor 详解）
- `BLOCKED_MODULES`：禁止导入 os、subprocess、sys、pathlib 等
- `BLOCKED_NAMES`：覆盖 open、exec、eval、compile、__import__ 等
- `GUARD_PREAMBLE`：在子进程代码前注入安全守卫（模块级预计算）
- `asyncio.create_subprocess_exec`：异步执行，不阻塞事件循环
- 受限环境变量：仅 PATH（Python 目录）、TEMP、TMP
- 输出大小限制：stdout 10KB，stderr 5KB

## 5. 记忆系统

### 三层记忆
| 类型 | 文件 | 存储 | 用途 |
|------|------|------|------|
| 短期 | `short_term.py` | deque | 最近 N 条对话缓冲 |
| 长期 | `long_term.py` | ChromaDB | 语义检索历史对话 |
| 工作 | `working.py` | dict | 当前任务上下文 |

### 记忆管理
- `MemoryManager`（`core/memory/manager.py`）：统一入口
- `get_context(task_id, query)`：组装三层记忆上下文
- `store_interaction(entry)`：存储对话到短期 + 长期记忆
- `MemoryEntry`（`core/memory/base.py`）：统一数据结构

## 6. 后端工程

### FastAPI
- 应用工厂模式（`main.py`）：`create_app()` + lifespan
- CORS 中间件配置
- 全局异常处理器：`AppError` → JSON 响应
- Swagger 自动生成：http://localhost:8000/docs

### 依赖注入
- `deps.py`：`DatabaseSession = Annotated[AsyncSession, Depends(get_db)]`
- `CurrentUser`：从 JWT Bearer Token 解析用户
- 类型别名注入，FastAPI 自动解析

### 数据库
- SQLAlchemy 2.0 Async + aiosqlite（`infrastructure/database.py`）
- `get_db()` 使用 `session.begin()` 自动事务管理
- ORM 模型继承 `BaseModel`（UUID PK, timestamps）
- `lazy="raise"` 防止异步隐式加载
- `updated_at` 通过 `event.listens_for` 自动更新
- Alembic 迁移管理

### 认证
- JWT 令牌（`infrastructure/security.py`）
- bcrypt 密码哈希
- Access Token + Refresh Token 双令牌机制
- Schema 验证：`Field(min_length=, max_length=)` 约束

### API 设计
- RESTful 资源路由
- 分页：`page` + `page_size` 查询参数，返回 `{items, total, page, page_size}`
- 流式文件上传：64KB chunks，实时大小检查
- 后台任务：FastAPI `BackgroundTasks` 处理 RAG 文档处理

## 7. 可观测性

### Token 追踪
- `TokenTracker`（`core/token_tracker.py`）
- `record(task_id, agent_name, model_name, prompt_tokens, completion_tokens)`
- `get_task_summary(task_id)`：按任务汇总
- `get_total_summary()`：全局汇总（总 token、总成本、总调用数）

### 执行 Trace
- `ExecutionTracer`（`core/execution_tracer.py`）
- `start_trace(task_id)` → `agent_start()` → `agent_end()` → `error()`
- `get_summary(task_id)`：返回结构化 trace 数据
- 按插入顺序淘汰旧任务

### Dashboard
- Gradio Dashboard 页面展示 Token 统计、成本估算、调用次数
- 支持按任务查看执行 Trace

## 8. 前端

### Gradio
- 多页面布局（`frontend/app.py`）：Chat、Documents、Tasks、Dashboard、Demo
- 全局 Orchestrator 单例（`get_orchestrator()`）
- 唯一 task_id（`uuid.uuid4().hex[:8]`）避免 trace 混淆
- 异步回调处理

### 5 个页面
| 页面 | 功能 |
|------|------|
| Chat | 对话交互，支持 Agent 模式和迭代次数配置 |
| Documents | 文档上传，后台 RAG 处理 |
| Tasks | 任务创建、执行、Trace 查看 |
| Dashboard | Token 统计、成本看板 |
| Demo | 预置示例，无需 API Key |

## 9. 测试

### 测试结构
```
tests/
├── conftest.py              # 共享 fixtures（client, auth_headers, setup_db）
├── unit/                    # 单元测试
│   ├── test_tools.py        # 工具测试
│   ├── test_agents.py       # Agent 测试
│   ├── test_chunker.py      # 分块测试
│   ├── test_memory.py       # 记忆测试
│   ├── test_token_tracker.py
│   ├── test_execution_tracer.py
│   ├── test_code_executor_sandbox.py  # 沙箱安全测试
├── integration/             # 集成测试
│   ├── test_api_auth.py     # 认证 API
│   ├── test_api_projects.py # 项目 API（分页）
│   ├── test_api_tasks.py    # 任务 API
```

### 测试技术
- pytest-asyncio（`asyncio_mode = "auto"`）
- `httpx.AsyncClient` + `ASGITransport` 进程内测试 FastAPI
- `auth_headers` fixture：注册用户并返回 JWT headers

## 推荐学习顺序

1. **跑通后端 API**：启动服务 → 访问 /docs → 测试认证和 CRUD
2. **理解工具系统**：读 `base.py` → `registry.py` → `calculator.py` → `code_executor.py`
3. **学习 RAG Pipeline**：`document_processor.py` → `chunker.py` → `embedder.py` → `retriever.py` → `reranker.py` → `pipeline.py`
4. **深入 Agent 系统**：`state.py` → `base.py` → `orchestrator.py` → 各 Agent 实现
5. **记忆与协作**：`memory/` → `collaboration/`
6. **可观测性**：`token_tracker.py` → `execution_tracer.py`
7. **前端与集成**：`frontend/app.py` → 运行 Demo 页面
8. **扩展实践**：添加新工具、新 Agent、新的检索策略

## 面试高频问题

基于本项目可以准备的面试问题：

1. **RAG 检索质量如何优化？** → Hybrid Search + Reranker + Query Expansion + Contextual Compression
2. **多 Agent 如何协调？** → LangGraph StateGraph + 条件边 + 反思循环
3. **如何保证异步性能？** → `asyncio.to_thread` 包装同步 I/O、`asyncio.gather` 并行执行
4. **工具系统如何扩展？** → `BaseTool` ABC + `ToolRegistry` + 自动 LangChain 桥接
5. **数据库事务如何管理？** → `session.begin()` 上下文管理器自动 commit/rollback
6. **沙箱安全如何实现？** → 模块级黑名单 + 内置函数覆盖 + 受限环境变量 + 异步子进程
