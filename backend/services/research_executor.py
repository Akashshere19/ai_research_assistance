
from services.tools.search_tool import web_search


def execute_research_questions(questions: list[str]) -> list[dict]:
    research_results = []

    for question in questions:
        result = web_search.invoke({"query": question})

        research_results.append({
            "question": question,
            "result": result,
        })

    return research_results
