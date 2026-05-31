"""Agent execution schemas."""

from datetime import datetime

from pydantic import BaseModel


class AgentExecutionResponse(BaseModel):
    id: str
    task_id: str
    agent_name: str
    status: str
    input_data: dict
    output_data: dict | None
    tool_calls_made: list
    token_usage: dict
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    duration_ms: int | None

    model_config = {"from_attributes": True}


class TokenUsageResponse(BaseModel):
    task_id: str
    agent_name: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float

    model_config = {"from_attributes": True}
