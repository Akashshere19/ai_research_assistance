from langchain_core.tools import StructuredTool
from ddgs.exceptions import DDGSException
from pydantic import BaseModel, Field
from ddgs import DDGS
import time


class WebSearchInput(BaseModel):
    query: str = Field(
        description="The search query to use when searching the web."
    )


def web_search_func(query: str) -> str:
    """Search the web and return relevant results for a research question."""
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        try:
            results = DDGS(timeout=10).text(
                query,
                max_results=5
            )

            if not results:
                return "No search results found."

            return "\n\n".join(
                f"Title: {result['title']}\n"
                f"URL: {result['href']}\n"
                f"Snippet: {result['body']}"
                for result in results
            )

        except DDGSException:
            if attempt == max_attempts:
                raise

            time.sleep(attempt)


web_search = StructuredTool.from_function(
    func=web_search_func,
    name="web_search",
    description="Search the web for information needed to answer a research question.",
    args_schema=WebSearchInput,
)