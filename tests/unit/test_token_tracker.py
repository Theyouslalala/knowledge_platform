"""Unit tests for TokenTracker."""

from src.knowledge_platform.core.token_tracker import TokenTracker


def test_record_token_usage():
    tracker = TokenTracker()
    record = tracker.record(
        task_id="t1",
        agent_name="planner",
        model_name="gpt-4o",
        prompt_tokens=100,
        completion_tokens=50,
    )
    assert record.total_tokens == 150
    assert record.estimated_cost_usd > 0


def test_task_summary():
    tracker = TokenTracker()
    tracker.record("t1", "planner", "gpt-4o", 100, 50)
    tracker.record("t1", "researcher", "gpt-4o-mini", 200, 100)

    summary = tracker.get_task_summary("t1")
    assert summary["total_tokens"] == 450
    assert summary["total_calls"] == 2
    assert "planner" in summary["by_agent"]
    assert "researcher" in summary["by_agent"]


def test_total_summary():
    tracker = TokenTracker()
    tracker.record("t1", "planner", "gpt-4o", 100, 50)
    tracker.record("t2", "researcher", "gpt-4o-mini", 200, 100)

    summary = tracker.get_total_summary()
    assert summary["total_records"] == 2
    assert summary["total_tokens"] == 450


def test_max_records_trimming():
    tracker = TokenTracker()
    tracker.MAX_RECORDS = 10
    for i in range(15):
        tracker.record(f"t{i}", "agent", "gpt-4o", 10, 5)
    assert len(tracker._records) <= 10


def test_max_tasks_trimming():
    tracker = TokenTracker()
    tracker.MAX_TASKS = 5
    for i in range(10):
        tracker.record(f"t{i}", "agent", "gpt-4o", 10, 5)
    assert len(tracker._task_records) <= 5


def test_unknown_model_zero_cost():
    tracker = TokenTracker()
    record = tracker.record("t1", "agent", "unknown-model", 100, 50)
    assert record.estimated_cost_usd == 0.0
