"""Researcher agent: information gathering with RAG and web search."""

from .base import BaseAgent
from .prompts import RESEARCHER_PROMPT
from .state import AgentState


class ResearchAgent(BaseAgent):
    def __init__(self, llm, tools: list = None):
        super().__init__(name="researcher", llm=llm, tools=tools, system_prompt=RESEARCHER_PROMPT)

    async def execute(self, state: AgentState) -> dict:
        previous = "\n".join(state.get("research_results", []))

        prompt = self.system_prompt.format(
            plan=state.get("plan", ""),
            user_query=state["user_query"],
            previous_research=previous,
        )

        tool_results = []
        for tool in self.tools:
            try:
                result = await tool.execute(query=state["user_query"])
                if result.success:
                    tool_results.append(f"[{tool.name}] {result.output}")
            except Exception as e:
                tool_results.append(f"[{tool.name}] Error: {e}")

        context = prompt + "\n\nTool Results:\n" + "\n".join(tool_results)
        response = await self.llm.ainvoke(context)

        new_results = state.get("research_results", []) + [response.content]

        return {
            "research_results": new_results,
            "current_agent": "analyst",
            "messages": [
                {
                    "role": "agent",
                    "content": response.content,
                    "agent_name": "researcher",
                    "tool_calls": None,
                }
            ],
        }
