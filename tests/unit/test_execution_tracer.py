"""Unit tests for ExecutionTracer."""

from src.knowledge_platform.core.execution_tracer import (
    ExecutionTracer,
    TraceEvent,
    TraceEventType,
)


def test_start_trace():
    tracer = ExecutionTracer()
    tracer.start_trace("t1")
    assert "t1" in tracer._traces
    assert tracer._traces["t1"] == []


def test_agent_start_end():
    tracer = ExecutionTracer()
    tracer.start_trace("t1")
    tracer.agent_start("t1", "planner")
    tracer.agent_end("t1", "planner", duration_ms=100.0)

    events = tracer.get_trace("t1")
    assert len(events) == 2
    assert events[0].event_type == TraceEventType.AGENT_START
    assert events[1].event_type == TraceEventType.AGENT_END
    assert events[1].duration_ms == 100.0


def test_tool_call_and_result():
    tracer = ExecutionTracer()
    tracer.start_trace("t1")
    tracer.tool_call("t1", "researcher", "rag_retrieval", {"query": "test"})
    tracer.tool_result("t1", "researcher", "rag_retrieval", "result text")

    events = tracer.get_trace("t1")
    assert len(events) == 2
    assert events[0].data["tool"] == "rag_retrieval"


def test_error_event():
    tracer = ExecutionTracer()
    tracer.start_trace("t1")
    tracer.error("t1", "planner", "Something went wrong")

    events = tracer.get_trace("t1")
    assert len(events) == 1
    assert events[0].event_type == TraceEventType.ERROR
    assert events[0].data["error"] == "Something went wrong"


def test_get_summary():
    tracer = ExecutionTracer()
    tracer.start_trace("t1")
    tracer.agent_start("t1", "planner")
    tracer.agent_end("t1", "planner", duration_ms=50.0)
    tracer.tool_call("t1", "researcher", "web_search", {})
    tracer.error("t1", "writer", "oops")

    summary = tracer.get_summary("t1")
    assert summary["total_events"] == 4
    assert summary["tool_calls"] == 1
    assert summary["errors"] == 1
    assert "planner" in summary["agents_involved"]


def test_max_events_trimming():
    tracer = ExecutionTracer()
    tracer.MAX_EVENTS_PER_TASK = 10
    tracer.start_trace("t1")
    for i in range(15):
        tracer.record(
            "t1",
            TraceEvent(event_type=TraceEventType.LLM_CALL, agent_name="agent"),
        )
    assert len(tracer.get_trace("t1")) <= 10


def test_max_tasks_trimming():
    tracer = ExecutionTracer()
    tracer.MAX_TASKS = 5
    for i in range(10):
        tracer.start_trace(f"t{i}")
    assert len(tracer._traces) <= 5
