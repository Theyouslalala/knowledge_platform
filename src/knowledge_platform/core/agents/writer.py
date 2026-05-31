"""Writer agent: synthesis and formatting."""

from .base import BaseAgent
from .prompts import WRITER_PROMPT
from .state import AgentState


class WriterAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(name="writer", llm=llm, system_prompt=WRITER_PROMPT)

    async def execute(self, state: AgentState) -> dict:
        research = "\n".join(state.get("research_results", []))

        prompt = self.system_prompt.format(
            user_query=state["user_query"],
            plan=state.get("plan", ""),
            research_results=research,
            analysis=state.get("analysis", ""),
            previous_draft=state.get("draft", ""),
            critique=state.get("critique", ""),
        )

        response = await self.llm.ainvoke(prompt)

        return {
            "draft": response.content,
            "current_agent": "critic",
            "status": "reviewing",
            "messages": [
                {
                    "role": "agent",
                    "content": response.content,
                    "agent_name": "writer",
                    "tool_calls": None,
                }
            ],
        }
