from services.agent_graph import graph


def run_research_agent(request):
    result = graph.invoke({
        "messages": [
            {
                "role": "user",
                "content": request
            }
        ]
    })

    return result["messages"][-1].content