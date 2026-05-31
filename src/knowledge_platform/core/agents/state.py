"""Agent state definition for LangGraph workflow."""

import operator
from typing import Annotated, Literal, TypedDict


class AgentMessage(TypedDict):
    role: Literal["user", "assistant", "system", "agent"]
    content: str
    agent_name: str | None
    tool_calls: list[dict] | None


class AgentState(TypedDict):
    task_id: str
    user_query: str
    messages: Annotated[list[AgentMessage], operator.add]
    current_agent: str
    plan: str | None
    research_results: list[str]
    analysis: str | None
    draft: str | None
    critique: str | None
    iteration: int
    max_iterations: int
    status: Literal["planning", "executing", "reviewing", "revising", "completed"]
    final_output: str | None
    metadata: dict
