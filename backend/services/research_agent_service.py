from langchain_core.messages import HumanMessage
from services.agent_graph import graph



def run_research_agent(
    question,
    project_id,
    allowed_document_ids=None,
        agent_run_id=None,
        user_id=None,

):
    
    result = graph.invoke(
    {
        "messages": [HumanMessage(content=question)],
        "project_id": str(project_id),
        "user_id":user_id,
        "allowed_document_ids": [
            str(document_id)
            for document_id in (allowed_document_ids or [])
        ],
        "document_results": [],
    },
    config={
    "configurable": {
        "thread_id": str(agent_run_id)
    }
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

    return {
        "report": report.model_dump_json(indent=2),
        "agent_trace": agent_trace,
    }
