from langchain_core.messages import HumanMessage
from services.agent_graph import graph


def run_research_agent(question):
    result = graph.invoke({
        "messages": [
            HumanMessage(content=question)
        ]
    })

    return result["messages"][-1].content