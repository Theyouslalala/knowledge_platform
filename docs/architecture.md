# 架构详解

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    Gradio Frontend                    │
│  Chat │ Documents │ Tasks │ Dashboard │ Demo          │
└─────────────────────┬───────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────┴───────────────────────────────┐
│                  FastAPI Backend                      │
│  Auth │ Projects │ Tasks │ Documents │ Export │ Search│
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
│  └────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────┐
│               Infrastructure                         │
│  SQLite │ ChromaDB │ JWT │ Cache │ Logging           │
└─────────────────────────────────────────────────────┘
```

## 关键设计决策

### 1. LangGraph vs asyncio 编排

选择 LangGraph 的原因：
- 声明式图定义，易于理解和修改
- 内置条件边支持反思循环
- 状态管理清晰（TypedDict）
- 支持检查点和恢复

### 2. Hybrid Search

三阶段检索 Pipeline：
1. Dense Retrieval（向量检索）- 语义相似度
2. BM25（稀疏检索）- 关键词匹配
3. Reciprocal Rank Fusion - 融合两路结果
4. Cross-encoder Reranker - 精排

### 3. 反思循环

```
Planner → Researcher → Analyst → Writer → Critic
                ↑                              │
                └──────── FAIL ────────────────┘
                                    │
                                  PASS → END
```

- max_iterations 防止无限循环
- Critic 输出结构化评估（PASS/FAIL + 反馈）
- 失败时带反馈回到 Researcher 重新检索

### 4. 工具系统

插件化设计：
- BaseTool 抽象接口
- ToolRegistry 注册表
- to_langchain_tool() 桥接 LangChain
- 新工具只需实现 execute() 方法

### 5. 记忆系统

三层记忆架构：
- 短期：最近对话（deque 缓冲）
- 长期：语义检索（ChromaDB 向量存储）
- 工作：当前任务上下文（字典）
