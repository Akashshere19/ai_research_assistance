from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from services.agent_state import AgentState
from services.agent_nodes import (call_llm, should_continue,
                                  generate_final_answer,plan_research, 
                                  execute_research,)
from services.tools.capital_tool import get_capital
from services.tools.search_tool import web_search





graph_builder = StateGraph(AgentState)
graph_builder.add_node("planner", plan_research)
graph_builder.add_node("researcher", execute_research)
graph_builder.add_node("report_writer", generate_final_answer)

graph_builder.add_edge(START, "planner")
graph_builder.add_edge("planner", "researcher")
graph_builder.add_edge("researcher", "report_writer")
graph_builder.add_edge("report_writer", END)

graph_builder.add_conditional_edges(
    "llm",
    should_continue,
    {
        "tools": "tools",
        "end": "final_answer",
    },
)

graph_builder.add_edge("tools", "llm")
graph_builder.add_edge("final_answer", END)

graph = graph_builder.compile()


