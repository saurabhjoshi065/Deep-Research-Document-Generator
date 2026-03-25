"""Wikipedia search tool."""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class SearchResult:
    """Search result."""
    title: str
    url: str
    snippet: str
    source: str = "wikipedia"
    rank: int = 0

    def to_dict(self) -> Dict:
        return {"title": self.title, "url": self.url, "snippet": self.snippet, "source": self.source, "rank": self.rank}

class SearchTool(ABC):
    """Base search tool."""
    def __init__(self, config=None):
        from src.config import get_config
        self.config = config or get_config().search
        self._last_request_time: float = 0
        self._min_delay: float = 1.0

    @abstractmethod
    def search(self, query: str, num_results: Optional[int] = None) -> List[SearchResult]:
        pass

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_delay: time.sleep(self._min_delay - elapsed)
        self._last_request_time = time.time()

class WikipediaSearch(SearchTool):
    """Wikipedia search."""
    def __init__(self, config=None):
        super().__init__(config)
        from src.tools.wikipedia import WikipediaTool
        self.wiki = WikipediaTool()

    def search(self, query: str, num_results: Optional[int] = None) -> List[SearchResult]:
        num_results = num_results or self.config.max_results
        results = self.wiki.search(query, num_results)
        for i, res in enumerate(results): res.rank = i
        return results

def create_search_tool(config=None) -> SearchTool:
    """Create Wikipedia search tool."""
    return WikipediaSearch(config)

def search_with_fallback(query: str, primary=None, fallback=None, num_results: int = 10) -> List[SearchResult]:
    """Search with Wikipedia."""
    tool = primary or create_search_tool()
    return tool.search(query, num_results)
