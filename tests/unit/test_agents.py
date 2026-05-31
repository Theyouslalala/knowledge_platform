"""Unit tests for agent system."""

from src.knowledge_platform.core.agents.state import AgentState


def test_agent_state_structure():
    state: AgentState = {
        "task_id": "test-123",
        "user_query": "test query",
        "messages": [],
        "current_agent": "planner",
        "plan": None,
        "research_results": [],
        "analysis": None,
        "draft": None,
        "critique": None,
        "iteration": 0,
        "max_iterations": 3,
        "status": "planning",
        "final_output": None,
        "metadata": {},
    }
    assert state["task_id"] == "test-123"
    assert state["status"] == "planning"
    assert state["iteration"] == 0
