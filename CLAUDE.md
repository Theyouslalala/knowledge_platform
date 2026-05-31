# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Knowledge-Enhanced Multi-Agent Collaboration Platform. A full-stack LLM application demonstrating multi-agent orchestration (LangGraph), RAG pipeline (ChromaDB + BM25 + RRF), tool systems, memory management, and a Gradio frontend.

## Common Commands

All commands run inside the `knowledge_platform` conda environment (Python 3.11).

```bash
# Install
conda activate knowledge_platform
pip install -e ".[dev]"

# Run backend (FastAPI on :8000)
uvicorn src.knowledge_platform.main:app --reload

# Run frontend (Gradio on :7860)
python -m src.knowledge_platform.frontend.app

# Tests
pytest tests/ -v                    # all tests
pytest tests/unit/ -v               # unit only
pytest tests/unit/test_tools.py -v  # single file
pytest -k test_calculator -v        # single test by name

# Lint
ruff check src/ tests/
ruff format --check src/ tests/
ruff check --fix src/ tests/ && ruff format src/ tests/  # auto-fix

# Database
alembic upgrade head  # apply migrations
```

## Architecture

### Layered Structure

```
Gradio Frontend (frontend/app.py)
    │
FastAPI Backend (main.py → api/router.py /api/v1/*)
    │
API Routes (api/)  ←── DI: DatabaseSession, CurrentUser (api/deps.py)
    │
Core Business Logic (core/)
    ├── agents/     LangGraph StateGraph orchestrator
    ├── rag/        Document → Chunk → Embed → Retrieve → Rerank
    ├── memory/     Short-term / Long-term / Working
    ├── tools/      Plugin registry (BaseTool → ToolRegistry)
    └── collaboration/  MessageBus, ReflectionEngine
    │
Infrastructure (infrastructure/)
    database.py    Async SQLAlchemy + aiosqlite
    security.py    JWT + bcrypt
    exceptions.py  AppError hierarchy
```

### Agent Orchestration (LangGraph)

The `AgentOrchestrator` builds a `StateGraph` with conditional edges:

```
Planner → Researcher → Analyst → Writer → Critic
                ↑                              │
                └──── FAIL (with feedback) ─────┘
                                    │
                                  PASS → END
```

- `AgentState` (TypedDict) is shared across all nodes; `messages` uses `operator.add` reducer
- `max_iterations` prevents infinite reflection loops
- LLM tier: `"full"` (gpt-4o) for Planner/Critic, `"mini"` (gpt-4o-mini) for specialists

### RAG Pipeline

Three-stage retrieval:
1. **Dense** (ChromaDB vector search) + **BM25** (keyword) → **Reciprocal Rank Fusion**
2. **Cross-encoder Reranker** (sentence-transformers)
3. **Contextual Compression** (LLM extracts relevant passages)

`QueryExpander` generates multiple search queries from the original question before retrieval.

### Key Patterns

- **Config**: Single `Settings` class in `config.py` loaded from `.env` via pydantic-settings
- **DI**: `DatabaseSession` and `CurrentUser` are `Annotated` type aliases in `api/deps.py`
- **ORM**: All models inherit `BaseModel` (UUID string PK, `created_at`/`updated_at`). Relationships use `lazy="selectin"`
- **Tools**: `BaseTool` ABC with `to_langchain_tool()` bridge. `ToolRegistry` is a class-level singleton
- **Exceptions**: `AppError` base → typed subclasses. Global handler returns `{"error": code, "message": msg}`
- **LLM Provider**: `LLMProvider` class caches instances by tier. `get_llm("mini")` / `get_llm("full")`

## Environment Setup

Copy `.env.example` to `.env`. Key settings:
- `OPENAI_API_KEY` or `DEEPSEEK_API_KEY` — required for LLM calls
- `SECRET_KEY` — change from default for JWT
- `DEMO_MODE=true` — run without API keys (limited functionality)

Data directories (`data/`) are auto-created and gitignored: SQLite DB, ChromaDB vectors, uploaded files.

## Testing

pytest-asyncio with `asyncio_mode = "auto"`. The `client` fixture uses `httpx.AsyncClient` with `ASGITransport` for in-process FastAPI testing. Tests are in `tests/unit/`, `tests/integration/`, `tests/e2e/`.
