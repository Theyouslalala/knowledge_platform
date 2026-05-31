"""Planner agent: task decomposition."""

from .base import BaseAgent
from .prompts import PLANNER_PROMPT
from .state import AgentState


class PlannerAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(name="planner", llm=llm, system_prompt=PLANNER_PROMPT)

    async def execute(self, state: AgentState) -> dict:
        prompt = self.system_prompt.format(user_query=state["user_query"])
        response = await self.llm.ainvoke(prompt)

        return {
            "plan": response.content,
            "current_agent": "researcher",
            "status": "executing",
            "messages": [
                {
                    "role": "agent",
                    "content": response.content,
                    "agent_name": "planner",
                    "tool_calls": None,
                }
            ],
        }
