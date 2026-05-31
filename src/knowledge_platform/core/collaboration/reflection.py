"""Self-reflection and critique loop utilities."""


class ReflectionEngine:
    def __init__(self, llm=None):
        self._llm = llm

    async def self_reflect(self, task: str, output: str, criteria: list[str] = None) -> dict:
        if self._llm is None:
            return {"score": 0.5, "feedback": "No LLM available for reflection"}

        criteria = criteria or ["accuracy", "completeness", "clarity"]
        criteria_text = "\n".join(f"- {c}" for c in criteria)

        prompt = f"""Evaluate this output on a scale of 0-1 for each criterion.

Task: {task}
Output: {output[:2000]}

Criteria:
{criteria_text}

Respond in format:
Score: X.X
Feedback: [brief feedback]"""

        try:
            response = await self._llm.ainvoke(prompt)
            text = response.content

            score = 0.5
            if "Score:" in text:
                try:
                    score_str = text.split("Score:")[1].strip().split()[0]
                    score = float(score_str)
                except (ValueError, IndexError):
                    pass

            feedback = ""
            if "Feedback:" in text:
                feedback = text.split("Feedback:")[1].strip()

            return {"score": score, "feedback": feedback}
        except Exception as e:
            return {"score": 0.0, "feedback": f"Reflection error: {e}"}
