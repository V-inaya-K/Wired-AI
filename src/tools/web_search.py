"""Tavily search wrapper."""

from __future__ import annotations

from typing import Any


class WebSearchTool:
    """Web search tool backed by Tavily."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        if not self._api_key:
            return []
        from tavily import TavilyClient

        client = TavilyClient(api_key=self._api_key)
        response = client.search(query=query, max_results=max_results, include_answer=True)
        return response.get("results", [])

