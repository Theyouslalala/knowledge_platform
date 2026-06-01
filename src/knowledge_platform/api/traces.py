"""Execution trace and token usage API endpoints."""

from fastapi import APIRouter

from ..core.execution_tracer import tracer as execution_tracer
from ..core.token_tracker import tracker as token_tracker
from ..infrastructure.exceptions import NotFoundError
from .deps import CurrentUser

router = APIRouter(prefix="/traces", tags=["Traces"])


@router.get("/{task_id}")
async def get_trace(task_id: str, user: CurrentUser):
    events = execution_tracer.get_trace(task_id)
    if not events:
        raise NotFoundError("Trace", task_id)
    summary = execution_tracer.get_summary_from_events(events)
    return {
        "task_id": task_id,
        "summary": summary,
        "events": [
            {
                "event_type": e.event_type.value,
                "agent_name": e.agent_name,
                "data": e.data,
                "timestamp": e.timestamp.isoformat(),
                "duration_ms": e.duration_ms,
            }
            for e in events
        ],
    }


@router.get("/{task_id}/tokens")
async def get_token_usage(task_id: str, user: CurrentUser):
    return token_tracker.get_task_summary(task_id)


@router.get("/tokens/summary")
async def get_token_summary(user: CurrentUser):
    return token_tracker.get_total_summary()
