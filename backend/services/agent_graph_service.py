from services.agent_graph import graph
from langchain_core.messages import HumanMessage


# def run_research_agent(request):
#     result = graph.invoke({
#         "messages": [
#             {
#                 "role": "user",
#                 "content": request
#             }
#         ]
#     })

#     return result["messages"][-1].content

def run_research_agent(question: str):
    result = graph.invoke({
        "messages": [HumanMessage(content=question)]
    })

    report = result.get("report")

    if report is None:
        raise ValueError("Research graph did not generate a report.")

    return report.model_dump_json(indent=2)