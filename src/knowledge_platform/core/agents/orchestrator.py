"""Agent orchestrator using LangGraph StateGraph."""

from langgraph.graph import END, StateGraph

from .analyst import AnalystAgent
from .critic import CriticAgent
from .llm_provider import get_llm
from .planner import PlannerAgent
from .researcher import ResearchAgent
from .state import AgentState
from .writer import WriterAgent
from ..tools.calculator import CalculatorTool
from ..tools.rag_tool import RAGRetrievalTool
from ..tools.web_search import WebSearchTool


class AgentOrchestrator:
    def __init__(self, llm_provider=None, tools: dict = None):
        self.llm_provider = llm_provider or get_llm
        self.tools = tools or {}
        self.agents = self._create_agents()
        self.graph = self._build_graph()

    def _create_agents(self) -> dict:
        llm_full = self.llm_provider("full")
        llm_mini = self.llm_provider("mini")

        rag_tool = self.tools.get("rag", RAGRetrievalTool())
        web_tool = self.tools.get("web_search", WebSearchTool())
        calc_tool = self.tools.get("calculator", CalculatorTool())

        return {
            "planner": PlannerAgent(llm_full),
            "researcher": ResearchAgent(llm_mini, tools=[rag_tool, web_tool]),
            "analyst": AnalystAgent(llm_mini, tools=[calc_tool]),
            "writer": WriterAgent(llm_mini),
            "critic": CriticAgent(llm_full),
        }

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)

        workflow.add_node("planner", self._run_planner)
        workflow.add_node("researcher", self._run_researcher)
        workflow.add_node("analyst", self._run_analyst)
        workflow.add_node("writer", self._run_writer)
        workflow.add_node("critic", self._run_critic)

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

    async def _run_planner(self, state: AgentState) -> dict:
        return await self.agents["planner"].execute(state)

    async def _run_researcher(self, state: AgentState) -> dict:
        return await self.agents["researcher"].execute(state)

    async def _run_analyst(self, state: AgentState) -> dict:
        return await self.agents["analyst"].execute(state)

    async def _run_writer(self, state: AgentState) -> dict:
        return await self.agents["writer"].execute(state)

    async def _run_critic(self, state: AgentState) -> dict:
        return await self.agents["critic"].execute(state)

    async def run(self, task_id: str, query: str, max_iterations: int = 3) -> AgentState:
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
            "metadata": {},
        }
        return await self.graph.ainvoke(initial_state)
