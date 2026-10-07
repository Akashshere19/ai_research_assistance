from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from ddgs import DDGS


class WebSearchInput(BaseModel):
    query: str = Field(
        description="The search query to use when searching the web."
    )


def web_search_func(query: str) -> str:
    """Search the web and return relevant results for a research question."""

    results = DDGS().text(
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


web_search = StructuredTool.from_function(
    func=web_search_func,
    name="web_search",
    description="Search the web for information needed to answer a research question.",
    args_schema=WebSearchInput,
)