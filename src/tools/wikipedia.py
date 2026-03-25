"""Wikipedia tool for research.

Provides structured access to Wikipedia content using the wikipedia library.
"""

import logging
from typing import List, Optional
import wikipedia

from src.tools.search import SearchResult

logger = logging.getLogger(__name__)

class WikipediaTool:
    """Tool for searching and fetching Wikipedia content."""

    def __init__(self, language: str = "en"):
        """Initialize the Wikipedia tool.

        Args:
            language: Wikipedia language code (default: en)
        """
        wikipedia.set_lang(language)

    def search(self, query: str, num_results: int = 3) -> List[SearchResult]:
        """Search Wikipedia and return formatted results.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of SearchResult objects
        """
        try:
            # 1. Get search results (page titles)
            search_results = wikipedia.search(query, results=num_results)
            
            results = []
            for title in search_results:
                try:
                    # 2. Fetch page summary
                    page = wikipedia.page(title, auto_suggest=False)
                    
                    results.append(SearchResult(
                        title=page.title,
                        url=page.url,
                        snippet=page.summary,  # Wikipedia uses snippet field for summary
                        source="wikipedia",
                        rank=len(results)
                    ))
                except wikipedia.exceptions.DisambiguationError as e:
                    # If multiple pages match, try the first option
                    try:
                        first_option = e.options[0]
                        page = wikipedia.page(first_option, auto_suggest=False)
                        results.append(SearchResult(
                            title=page.title,
                            url=page.url,
                            content=page.summary,
                            source="wikipedia",
                            rank=len(results)
                        ))
                    except:
                        continue
                except Exception as e:
                    logger.warning(f"Failed to fetch Wikipedia page '{title}': {e}")
                    continue
            
            return results

        except Exception as e:
            logger.error(f"Wikipedia search failed: {e}")
            return []

    def fetch_full_content(self, title: str) -> Optional[str]:
        """Fetch the full content of a Wikipedia page.

        Args:
            title: Page title

        Returns:
            Full page content or None
        """
        try:
            page = wikipedia.page(title, auto_suggest=False)
            return page.content
        except:
            return None
