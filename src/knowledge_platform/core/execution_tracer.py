"""Agent execution tracer for debugging and visualization."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class TraceEventType(str, Enum):
    AGENT_START = "agent_start"
    AGENT_END = "agent_end"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    LLM_CALL = "llm_call"
    STATE_UPDATE = "state_update"
    ERROR = "error"


@dataclass
class TraceEvent:
    event_type: TraceEventType
    agent_name: str
    data: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float | None = None


class ExecutionTracer:
    MAX_EVENTS_PER_TASK = 1000
    MAX_TASKS = 500

    def __init__(self):
        self._traces: dict[str, list[TraceEvent]] = {}

    def start_trace(self, task_id: str):
        self._traces[task_id] = []
        if len(self._traces) > self.MAX_TASKS:
            self._trim_tasks()

    def record(self, task_id: str, event: TraceEvent):
        if task_id not in self._traces:
            self._traces[task_id] = []
        self._traces[task_id].append(event)
        if len(self._traces[task_id]) > self.MAX_EVENTS_PER_TASK:
            self._traces[task_id] = self._traces[task_id][-self.MAX_EVENTS_PER_TASK // 2 :]

    def _trim_tasks(self):
        if len(self._traces) > self.MAX_TASKS:
            keys = list(self._traces.keys())
            to_remove = len(keys) - self.MAX_TASKS // 2
            for key in keys[:to_remove]:
                del self._traces[key]

    def agent_start(self, task_id: str, agent_name: str):
        self.record(
            task_id,
            TraceEvent(event_type=TraceEventType.AGENT_START, agent_name=agent_name),
        )

    def agent_end(self, task_id: str, agent_name: str, duration_ms: float = None):
        self.record(
            task_id,
            TraceEvent(
                event_type=TraceEventType.AGENT_END,
                agent_name=agent_name,
                duration_ms=duration_ms,
            ),
        )

    def tool_call(self, task_id: str, agent_name: str, tool_name: str, args: dict = None):
        self.record(
            task_id,
            TraceEvent(
                event_type=TraceEventType.TOOL_CALL,
                agent_name=agent_name,
                data={"tool": tool_name, "args": args or {}},
            ),
        )

    def tool_result(self, task_id: str, agent_name: str, tool_name: str, result: str):
        self.record(
            task_id,
            TraceEvent(
                event_type=TraceEventType.TOOL_RESULT,
                agent_name=agent_name,
                data={"tool": tool_name, "result": result[:500]},
            ),
        )

    def llm_call(self, task_id: str, agent_name: str, model: str, tokens: int = 0):
        self.record(
            task_id,
            TraceEvent(
                event_type=TraceEventType.LLM_CALL,
                agent_name=agent_name,
                data={"model": model, "tokens": tokens},
            ),
        )

    def error(self, task_id: str, agent_name: str, error: str):
        self.record(
            task_id,
            TraceEvent(
                event_type=TraceEventType.ERROR,
                agent_name=agent_name,
                data={"error": error},
            ),
        )

    def get_trace(self, task_id: str) -> list[TraceEvent]:
        return self._traces.get(task_id, [])

    def get_summary(self, task_id: str) -> dict:
        events = self.get_trace(task_id)
        if not events:
            return {"total_events": 0}

        agent_times = {}
        for e in events:
            if e.event_type == TraceEventType.AGENT_END and e.duration_ms:
                agent_times[e.agent_name] = agent_times.get(e.agent_name, 0) + e.duration_ms

        tool_calls = sum(1 for e in events if e.event_type == TraceEventType.TOOL_CALL)
        errors = sum(1 for e in events if e.event_type == TraceEventType.ERROR)

        return {
            "total_events": len(events),
            "tool_calls": tool_calls,
            "errors": errors,
            "agent_times_ms": agent_times,
            "agents_involved": list(set(e.agent_name for e in events)),
        }


tracer = ExecutionTracer()
