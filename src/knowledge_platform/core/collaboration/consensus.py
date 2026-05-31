"""Multi-agent consensus mechanism."""


class ConsensusEngine:
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold

    def vote(self, opinions: list[dict]) -> dict:
        if not opinions:
            return {"consensus": None, "confidence": 0.0}

        scores = [o.get("score", 0.5) for o in opinions]
        avg_score = sum(scores) / len(scores)

        feedbacks = [o.get("feedback", "") for o in opinions if o.get("feedback")]

        consensus = avg_score >= self.threshold

        return {
            "consensus": consensus,
            "confidence": avg_score,
            "num_opinions": len(opinions),
            "combined_feedback": "\n".join(feedbacks),
        }
