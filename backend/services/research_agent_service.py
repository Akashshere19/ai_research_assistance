from langchain_core.messages import HumanMessage
from services.agent_graph import graph


def run_research_agent(question):
    result = graph.invoke({
        "messages": [
            HumanMessage(content=question)
        ]
    })
    agent_trace = result.get("agent_trace", [])
    report = result.get("report")

    if report is None:
            quality = result.get("quality_check", {})
            reason = quality.get(
                "reason",
                "Research evidence was insufficient to generate a report.",
            )
            raise ValueError(reason)

    # return report.model_dump_json(indent=2)
    return {
    "report": report.model_dump_json(indent=2),
    "agent_trace": agent_trace,
}

    # return result["messages"][-1].content