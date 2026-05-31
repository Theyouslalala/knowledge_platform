"""RAG retrieval as a tool for agents."""

from .base import BaseTool, ToolResult


class RAGRetrievalTool(BaseTool):
    name = "knowledge_retrieval"
    description = "Search the knowledge base for relevant documents and information."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query for the knowledge base",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default 5)",
            },
        },
        "required": ["query"],
    }

    def __init__(self, retriever=None):
        self._retriever = retriever

    async def execute(self, query: str = "", top_k: int = 5, **kwargs) -> ToolResult:
        if self._retriever is None:
            return ToolResult(
                success=False,
                output="Knowledge base not configured. Please upload documents first.",
            )
        try:
            results = await self._retriever.retrieve(query, top_k=top_k)
            if not results:
                return ToolResult(success=True, output="No relevant documents found.")

            formatted = []
            for i, r in enumerate(results, 1):
                formatted.append(f"[{i}] (score: {r.score:.3f}) {r.content[:500]}")

            return ToolResult(success=True, output="\n\n".join(formatted))
        except Exception as e:
            return ToolResult(success=False, output=f"Retrieval error: {e}")
