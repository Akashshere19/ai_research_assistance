from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages
from services.research_report_schema import ResearchReport,ResearchAnalysis

class AgentState(TypedDict):
        messages: Annotated[list, add_messages]
        research_questions: list[str]
        research_results: list[dict]
        report: ResearchReport | None
        quality_check: dict
        revision_count: int
        revision_feedback: str          
        agent_trace: list[dict]
        analysis: ResearchAnalysis | None
