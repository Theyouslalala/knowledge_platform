"""Web search tool using httpx."""

import httpx

from ..config import get_settings
from .base import BaseTool, ToolResult

settings = get_settings()


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for information using a search engine API."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query",
            },
            "num_results": {
                "type": "integer",
                "description": "Number of results to return (default 5)",
            },
        },
        "required": ["query"],
    }

    async def execute(self, query: str = "", num_results: int = 5, **kwargs) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_redirect": "1"},
                )
                data = response.json()

            results = []
            if data.get("AbstractText"):
                results.append(f"Summary: {data['AbstractText']}")

            for topic in data.get("RelatedTopics", [])[:num_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    results.append(f"- {topic['Text']}")

            if not results:
                return ToolResult(success=True, output=f"No results found for: {query}")

            return ToolResult(success=True, output="\n".join(results))
        except Exception as e:
            return ToolResult(success=False, output=f"Search error: {e}")
