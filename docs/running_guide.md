# 运行指南

## 环境要求

- Python 3.11+
- Anaconda（推荐）
- Git

## 1. 克隆项目

```bash
git clone https://github.com/Theyouslalala/knowledge_platform.git
cd knowledge_platform
```

## 2. 创建 Conda 环境

```bash
conda create -n knowledge_platform python=3.11
conda activate knowledge_platform
```

## 3. 安装依赖

```bash
pip install -e ".[dev]"
```

安装内容：
- **运行依赖**: FastAPI, SQLAlchemy 2.0, LangChain, LangGraph, ChromaDB, sentence-transformers, Gradio, PyTorch
- **开发依赖**: pytest, pytest-asyncio, httpx, ruff

## 4. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，按需配置：

```ini
# ── LLM 配置（二选一）──

# OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL_GPT4O=gpt-4o
OPENAI_MODEL_GPT4O_MINI=gpt-4o-mini

# 或 DeepSeek（兼容 OpenAI API）
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# ── 安全 ──
SECRET_KEY=your-random-secret-key    # JWT 签名密钥，默认自动生成

# ── 数据库（默认即可）──
DATABASE_URL=sqlite+aiosqlite:///./data/knowledge_platform.db

# ── 向量数据库（默认即可）──
CHROMA_PERSIST_DIR=./data/chroma

# ── Embedding ──
EMBEDDING_PROVIDER=openai            # openai 或 local（本地 Sentence-Transformers）
EMBEDDING_MODEL=text-embedding-3-small

# ── CORS ──
CORS_ORIGINS=["http://localhost:7860","http://localhost:8000"]

# ── 演示模式 ──
DEMO_MODE=false                      # true 时无需 API Key（功能受限）
```

### LLM Provider 说明

项目支持两种 LLM Provider，通过 `config.py` 的 `Settings` 自动加载：

| Provider | 环境变量 | 适用场景 |
|----------|---------|---------|
| OpenAI | `OPENAI_API_KEY` | 默认，gpt-4o + gpt-4o-mini |
| DeepSeek | `DEEPSEEK_API_KEY` | 兼容 API，性价比高 |

Agent 双 Tier 模型分配：
- **full** tier（gpt-4o / deepseek-chat）：Planner、Critic — 需要深度推理
- **mini** tier（gpt-4o-mini）：Researcher、Analyst、Writer — 执行层

## 5. 初始化数据库

```bash
alembic upgrade head
```

> 首次启动 FastAPI 时，lifespan 会自动调用 `init_db()` 创建表结构。`alembic upgrade head` 用于应用迁移。

数据目录自动创建：
```
data/
├── knowledge_platform.db    # SQLite 数据库
├── chroma/                  # ChromaDB 向量存储
└── uploads/                 # 上传的文档文件
```

## 6. 启动后端（FastAPI）

```bash
uvicorn src.knowledge_platform.main:app --reload --host 0.0.0.0 --port 8000
```

| 地址 | 说明 |
|------|------|
| http://localhost:8000 | API 根路径 |
| http://localhost:8000/docs | Swagger UI（交互式 API 文档） |
| http://localhost:8000/redoc | ReDoc（阅读式 API 文档） |
| http://localhost:8000/health | 健康检查 |

### 健康检查响应示例

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected"
}
```

## 7. 启动前端（Gradio）

另开一个终端：

```bash
conda activate knowledge_platform
python -m src.knowledge_platform.frontend.app
```

访问 http://localhost:7860

### 5 个页面

| 页面 | 功能 |
|------|------|
| Chat | 对话交互，支持选择 Agent 模式和迭代次数 |
| Documents | 上传文档，自动 RAG 处理（分块 + 嵌入 + 存储） |
| Tasks | 创建任务、执行（后台 Agent）、查看 Trace |
| Dashboard | Token 用量统计、成本估算、调用次数 |
| Demo | 预置示例，无需 API Key 即可体验 |

## 8. 运行测试

```bash
# 全部测试
pytest tests/ -v

# 仅单元测试
pytest tests/unit/ -v

# 仅集成测试
pytest tests/integration/ -v

# 单个文件
pytest tests/unit/test_tools.py -v

# 按名称过滤
pytest -k test_calculator -v

# 显示覆盖率
pytest tests/ -v --tb=short
```

### 测试结构

```
tests/
├── conftest.py                      # 共享 fixtures（client, auth_headers, setup_db）
├── unit/
│   ├── test_tools.py                # 工具系统测试
│   ├── test_agents.py               # Agent 测试
│   ├── test_chunker.py              # 分块策略测试
│   ├── test_memory.py               # 记忆系统测试
│   ├── test_token_tracker.py        # Token 追踪测试
│   ├── test_execution_tracer.py     # 执行 Trace 测试
│   └── test_code_executor_sandbox.py # 沙箱安全测试
├── integration/
│   ├── test_api_auth.py             # 认证 API 测试
│   ├── test_api_projects.py         # 项目 API 测试（含分页）
│   └── test_api_tasks.py            # 任务 API 测试
└── e2e/                             # 端到端测试（预留）
```

### 测试技术栈

- **pytest-asyncio**: 异步测试支持，`asyncio_mode = "auto"`
- **httpx.AsyncClient + ASGITransport**: 进程内测试 FastAPI，无需启动服务器
- **auth_headers fixture**: 自动注册用户并返回 JWT headers

## 9. 代码检查

```bash
# 检查
ruff check src/ tests/
ruff format --check src/ tests/

# 自动修复
ruff check --fix src/ tests/
ruff format src/ tests/
```

ruff 规则配置（`pyproject.toml`）：
```toml
[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "B", "S", "A", "UP", "SIM"]
ignore = ["S101", "S603", "S607", "B008"]
```

## 10. 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "description"

# 应用迁移
alembic upgrade head

# 回滚一步
alembic downgrade -1

# 查看当前版本
alembic current
```

## 常见问题

### Q: 没有 API Key 能运行吗？

可以。设置 `DEMO_MODE=true`，前端 Demo 页面可以使用预置示例。但 Chat、Tasks 等需要 LLM 的功能会报错。

### Q: PyTorch 安装很慢怎么办？

```bash
# 使用清华镜像
pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或者只用 CPU 版本
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### Q: ChromaDB 数据在哪里？

`data/chroma/` 目录。删除此目录可清空所有向量数据。

### Q: 如何切换 LLM Provider？

编辑 `.env`，设置对应的 API Key 和 Base URL。例如切换到 DeepSeek：

```ini
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
```

代码中 `LLMProvider`（`core/agents/llm_provider.py`）会根据配置自动选择 Provider。

### Q: 端口被占用怎么办？

```bash
# 换一个端口
uvicorn src.knowledge_platform.main:app --reload --port 8001

# 前端同理
python -m src.knowledge_platform.frontend.app --server_port 7861
```
