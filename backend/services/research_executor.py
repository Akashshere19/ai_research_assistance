
from services.tools.search_tool import web_search



def execute_research_questions(questions: list[str],
                ) -> list[dict]:        
                            
    
    research_results = []

    for question in questions:
        try:
            result = web_search.invoke({"query": question})

            if not isinstance(result, str):
                result = str(result)

            research_results.append({
                "question": question,
                "result": result,
                "status": (
                    "SUCCESS"
                    if result.strip()
                    and result.strip() != "No search results found."
                    else "NO_RESULTS"
                ),
            })

        except Exception as exc:
            # Preserve the failure for this question so that
            # other research questions can still be processed.
            research_results.append({
                "question": question,
                "result": "",
                "status": "FAILED",
                "error": str(exc),
            })

    return research_results

