from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from services.agent_state import AgentState
from services.agent_nodes import call_llm, should_continue,generate_final_answer
from services.tools.capital_tool import get_capital
from services.tools.search_tool import web_search

graph_builder = StateGraph(AgentState)

graph_builder.add_node("llm", call_llm)
tool_node = ToolNode([get_capital,web_search])
graph_builder.add_node("tools", tool_node)
graph_builder.add_node("final_answer", generate_final_answer)
graph_builder.add_edge(START, "llm")
graph_builder.add_edge("tools", "final_answer")
graph_builder.add_conditional_edges(
    "llm",
    should_continue,
    {
        "tools": "tools",
        "end": END,
    }
)
graph = graph_builder.compile()

