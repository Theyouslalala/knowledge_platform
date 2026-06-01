"""Agent orchestrator using LangGraph StateGraph."""

import time

from langgraph.graph import END, StateGraph

from ..execution_tracer import tracer as execution_tracer
from ..memory.base import MemoryEntry
from ..memory.manager import MemoryManager
from ..tools.registry import ToolRegistry
from .analyst import AnalystAgent
from .critic import CriticAgent
from .llm_provider import get_llm
from .planner import PlannerAgent
from .researcher import ResearchAgent
from .state import AgentState
from .writer import WriterAgent


class AgentOrchestrator:
    def __init__(self, llm_provider=None, memory_manager: MemoryManager = None):
        self.llm_provider = llm_provider or get_llm
        self.memory = memory_manager or MemoryManager()
        self._ensure_tools_registered()
        self.agents = self._create_agents()
        self.graph = self._build_graph()

    @staticmethod
    def _ensure_tools_registered():
        if not ToolRegistry.get_all():
            from ..tools.calculator import CalculatorTool
            from ..tools.rag_tool import RAGRetrievalTool
            from ..tools.web_search import WebSearchTool

            for tool_cls in [CalculatorTool, RAGRetrievalTool, WebSearchTool]:
                ToolRegistry.register(tool_cls())

    def _create_agents(self) -> dict:
        llm_full = self.llm_provider("full")
        llm_mini = self.llm_provider("mini")

        rag_tool = ToolRegistry.get("knowledge_retrieval")
        web_tool = ToolRegistry.get("web_search")
        calc_tool = ToolRegistry.get("calculator")

        tools_map = {
            "researcher": [t for t in [rag_tool, web_tool] if t],
            "analyst": [t for t in [calc_tool] if t],
        }

        return {
            "planner": PlannerAgent(llm_full),
            "researcher": ResearchAgent(llm_mini, tools=tools_map["researcher"]),
            "analyst": AnalystAgent(llm_mini, tools=tools_map["analyst"]),
            "writer": WriterAgent(llm_mini),
            "critic": CriticAgent(llm_full),
        }

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        for name in self.agents:
            workflow.add_node(name, self._make_runner(name))

        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "analyst")
        workflow.add_edge("analyst", "writer")
        workflow.add_edge("writer", "critic")

        workflow.add_conditional_edges(
            "critic",
            self._route_after_critique,
            {"approve": END, "revise": "researcher"},
        )

        return workflow.compile()

    def _route_after_critique(self, state: AgentState) -> str:
        if state.get("status") == "completed":
            return "approve"
        if state.get("iteration", 0) >= state.get("max_iterations", 3):
            return "approve"
        return "revise"

    async def _run_agent_with_tracing(
        self, agent_name: str, state: AgentState
    ) -> dict:
        task_id = state.get("task_id", "unknown")
        execution_tracer.agent_start(task_id, agent_name)
        start = time.monotonic()
        try:
            result = await self.agents[agent_name].execute(state)
            duration_ms = (time.monotonic() - start) * 1000
            execution_tracer.agent_end(
                task_id, agent_name, duration_ms=duration_ms
            )
            return result
        except Exception as e:
            execution_tracer.error(task_id, agent_name, str(e))
            raise

    def _make_runner(self, agent_name: str):
        async def _run(state: AgentState) -> dict:
            return await self._run_agent_with_tracing(agent_name, state)
        return _run

    async def run(
        self, task_id: str, query: str, max_iterations: int = 3
    ) -> AgentState:
        execution_tracer.start_trace(task_id)

        memory_context = await self.memory.get_context(task_id, query)

        initial_state: AgentState = {
            "task_id": task_id,
            "user_query": query,
            "messages": [],
            "current_agent": "planner",
            "plan": None,
            "research_results": [],
            "analysis": None,
            "draft": None,
            "critique": None,
            "iteration": 0,
            "max_iterations": max_iterations,
            "status": "planning",
            "final_output": None,
            "metadata": {"memory_context": memory_context},
        }

        result = await self.graph.ainvoke(initial_state)

        await self.memory.store_interaction(
            MemoryEntry(
                content=f"Q: {query}\nA: {result.get('final_output', '')[:500]}",
                role="assistant",
                metadata={"task_id": task_id},
            )
        )

        return result


_orchestrator_instance = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = AgentOrchestrator()
    return _orchestrator_instance
