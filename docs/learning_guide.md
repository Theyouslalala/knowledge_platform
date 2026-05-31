# 学习路线

本项目覆盖以下核心技术点，按学习顺序排列。

## 1. LLM 基础

### Prompt Engineering
- System Prompt 设计（`core/agents/prompts.py`）
- Few-shot 示例
- Chain-of-Thought 引导推理

### LLM API 调用
- OpenAI API / 兼容 API（`core/agents/llm_provider.py`）
- 流式输出
- Token 计算和成本估算（`core/token_tracker.py`）

## 2. RAG (Retrieval-Augmented Generation)

### 文档处理
- 多格式解析：PDF、DOCX、TXT、MD（`core/rag/document_processor.py`）
- 分块策略：固定大小、递归、语义（`core/rag/chunker.py`）

### 向量检索
- Embedding 模型：OpenAI / Sentence-Transformers（`core/rag/embedder.py`）
- 向量数据库：ChromaDB（`core/rag/vector_store.py`）

### 高级检索
- Hybrid Search：Dense + BM25 + RRF（`core/rag/retriever.py`）
- Cross-encoder Reranker（`core/rag/reranker.py`）
- Query Expansion 查询扩展
- Contextual Compression 上下文压缩

## 3. Agent 系统

### Agent 架构
- BaseAgent 抽象（`core/agents/base.py`）
- ReAct 模式
- Plan-and-Execute 模式

### 多 Agent 协作
- LangGraph StateGraph（`core/agents/orchestrator.py`）
- 条件边和反思循环
- Agent 间通信（`core/collaboration/message_bus.py`）

### 5 个 Agent 角色
- Planner：任务拆解（`core/agents/planner.py`）
- Researcher：信息检索（`core/agents/researcher.py`）
- Analyst：数据分析（`core/agents/analyst.py`）
- Writer：内容生成（`core/agents/writer.py`）
- Critic：质量审查（`core/agents/critic.py`）

## 4. 工具系统

### 工具设计
- BaseTool 抽象（`core/tools/base.py`）
- 工具注册表（`core/tools/registry.py`）
- LangChain Tool 转换

### 内置工具
- 计算器（`core/tools/calculator.py`）
- 代码执行器（`core/tools/code_executor.py`）
- 文件操作（`core/tools/file_ops.py`）
- Web 搜索（`core/tools/web_search.py`）
- RAG 检索（`core/tools/rag_tool.py`）

## 5. 记忆系统

### 三种记忆
- 短期记忆：对话缓冲（`core/memory/short_term.py`）
- 长期记忆：向量存储（`core/memory/long_term.py`）
- 工作记忆：任务上下文（`core/memory/working.py`）

### 记忆管理
- 记忆协调器（`core/memory/manager.py`）
- 上下文组装策略

## 6. 后端工程

### FastAPI
- 应用工厂模式（`main.py`）
- 依赖注入（`api/deps.py`）
- 中间件和异常处理

### 数据库
- SQLAlchemy 2.0 Async（`infrastructure/database.py`）
- ORM 模型设计（`models/`）
- Alembic 迁移

### 认证
- JWT 令牌（`infrastructure/security.py`）
- 密码哈希（bcrypt）
- 刷新令牌机制

## 7. 可观测性

### Token 追踪
- 用量统计（`core/token_tracker.py`）
- 成本估算

### 执行 Trace
- Agent 执行记录（`core/execution_tracer.py`）
- 工具调用日志
- 性能分析

## 8. 前端

### Gradio
- 多页面布局（`frontend/app.py`）
- 实时对话界面
- 文件上传
- 数据可视化

## 推荐学习顺序

1. 先跑通后端 API（Phase 1-3）
2. 理解工具系统和记忆（Phase 4）
3. 学习 RAG Pipeline（Phase 5）
4. 深入 Agent 系统（Phase 6）
5. 了解追踪和前端（Phase 7-8）
6. 尝试修改和扩展功能
