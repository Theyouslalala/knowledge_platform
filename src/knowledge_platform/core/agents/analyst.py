"""Analyst agent: data analysis and reasoning."""

from .base import BaseAgent
from .prompts import ANALYST_PROMPT
from .state import AgentState


class AnalystAgent(BaseAgent):
    def __init__(self, llm, tools: list = None):
        super().__init__(name="analyst", llm=llm, tools=tools, system_prompt=ANALYST_PROMPT)

    async def execute(self, state: AgentState) -> dict:
        research = "\n".join(state.get("research_results", []))

        prompt = self.system_prompt.format(
            user_query=state["user_query"],
            research_results=research,
            previous_analysis=state.get("analysis", ""),
        )

        tool_results = []
        for tool in self.tools:
            try:
                result = await tool.execute(expression=research[:100])
                if result.success:
                    tool_results.append(f"[{tool.name}] {result.output}")
            except Exception:
                pass

        context = prompt
        if tool_results:
            context += "\n\nTool Results:\n" + "\n".join(tool_results)

        response = await self.llm.ainvoke(context)

        return {
            "analysis": response.content,
            "current_agent": "writer",
            "messages": [
                {
                    "role": "agent",
                    "content": response.content,
                    "agent_name": "analyst",
                    "tool_calls": None,
                }
            ],
        }
