from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from services.agent_state import AgentState
from services.agent_nodes import (revise_research_plan,
                                  generate_final_answer,plan_research, 
                                  execute_research,check_research_quality,analyze_research)
from services.checkpointer import create_checkpointer
from services.tools.capital_tool import get_capital
from services.tools.search_tool import web_search


def route_after_quality_check(state: AgentState):
    quality = state.get("quality_check", {})

    if quality.get("sufficient", False):
        return "analyst"

    if state.get("revision_count", 0) < 1:
        return "revise_plan"

    return "insufficient_evidence"



graph_builder = StateGraph(AgentState)
graph_builder.add_node("planner", plan_research)
graph_builder.add_node("researcher", execute_research)
graph_builder.add_node("analyst", analyze_research)
graph_builder.add_node("report_writer", generate_final_answer)
graph_builder.add_node("quality_checker", check_research_quality)
graph_builder.add_node("revise_plan", revise_research_plan)


graph_builder.add_edge(START, "planner")
graph_builder.add_edge("researcher", "quality_checker")
graph_builder.add_edge("planner", "researcher")


graph_builder.add_conditional_edges(
    "quality_checker",
    route_after_quality_check,
    {
        "analyst": "analyst",
        "report_writer": "report_writer",
        "revise_plan": "revise_plan",
        "insufficient_evidence": END,
    },
)

graph_builder.add_edge("revise_plan", "researcher")
graph_builder.add_edge("analyst", "report_writer")
graph_builder.add_edge("report_writer", END)

checkpointer = create_checkpointer()
graph = graph_builder.compile(checkpointer=checkpointer)




