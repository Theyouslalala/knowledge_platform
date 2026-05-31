"""Token usage tracking and cost estimation."""

from dataclasses import dataclass, field
from datetime import datetime, timezone

MODEL_PRICING = {
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "deepseek-chat": {"input": 0.14 / 1_000_000, "output": 0.28 / 1_000_000},
}


@dataclass
class TokenRecord:
    agent_name: str
    model_name: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TokenTracker:
    MAX_RECORDS = 10000

    def __init__(self):
        self._records: list[TokenRecord] = []
        self._task_records: dict[str, list[TokenRecord]] = {}

    def record(
        self,
        task_id: str,
        agent_name: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> TokenRecord:
        pricing = MODEL_PRICING.get(model_name, {"input": 0, "output": 0})
        cost = prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]

        record = TokenRecord(
            agent_name=agent_name,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            estimated_cost_usd=round(cost, 6),
        )

        self._records.append(record)
        if task_id not in self._task_records:
            self._task_records[task_id] = []
        self._task_records[task_id].append(record)

        if len(self._records) > self.MAX_RECORDS:
            self._records = self._records[-self.MAX_RECORDS // 2 :]

        return record

    def get_task_summary(self, task_id: str) -> dict:
        records = self._task_records.get(task_id, [])
        if not records:
            return {"total_tokens": 0, "total_cost": 0, "by_agent": {}}

        by_agent = {}
        for r in records:
            if r.agent_name not in by_agent:
                by_agent[r.agent_name] = {"tokens": 0, "cost": 0, "calls": 0}
            by_agent[r.agent_name]["tokens"] += r.total_tokens
            by_agent[r.agent_name]["cost"] += r.estimated_cost_usd
            by_agent[r.agent_name]["calls"] += 1

        return {
            "total_tokens": sum(r.total_tokens for r in records),
            "total_cost": round(sum(r.estimated_cost_usd for r in records), 6),
            "total_calls": len(records),
            "by_agent": by_agent,
        }

    def get_total_summary(self) -> dict:
        return {
            "total_records": len(self._records),
            "total_tokens": sum(r.total_tokens for r in self._records),
            "total_cost": round(sum(r.estimated_cost_usd for r in self._records), 6),
        }

    def get_records(self, task_id: str = None) -> list[TokenRecord]:
        if task_id:
            return self._task_records.get(task_id, [])
        return self._records.copy()


tracker = TokenTracker()
