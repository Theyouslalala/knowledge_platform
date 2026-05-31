"""Critic agent: quality evaluation and reflection."""

from .base import BaseAgent
from .prompts import CRITIC_PROMPT
from .state import AgentState


class CriticAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__(name="critic", llm=llm, system_prompt=CRITIC_PROMPT)

    async def execute(self, state: AgentState) -> dict:
        prompt = self.system_prompt.format(
            user_query=state["user_query"],
            plan=state.get("plan", ""),
            draft=state.get("draft", ""),
        )

        response = await self.llm.ainvoke(prompt)
        critique_text = response.content

        verdict = "FAIL"
        if "VERDICT: PASS" in critique_text.upper():
            verdict = "PASS"

        new_iteration = state.get("iteration", 0) + 1

        if verdict == "PASS" or new_iteration >= state.get("max_iterations", 3):
            return {
                "critique": critique_text,
                "final_output": state.get("draft", ""),
                "status": "completed",
                "iteration": new_iteration,
                "messages": [
                    {
                        "role": "agent",
                        "content": f"Critique (PASS):\n{critique_text}",
                        "agent_name": "critic",
                        "tool_calls": None,
                    }
                ],
            }
        else:
            return {
                "critique": critique_text,
                "current_agent": "researcher",
                "status": "revising",
                "iteration": new_iteration,
                "messages": [
                    {
                        "role": "agent",
                        "content": f"Critique (FAIL - revision {new_iteration}):\n{critique_text}",
                        "agent_name": "critic",
                        "tool_calls": None,
                    }
                ],
            }
