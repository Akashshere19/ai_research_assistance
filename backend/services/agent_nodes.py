from .agent_state import AgentState
from langchain_core.messages import SystemMessage
from .llm_service import generate_response
from services.llm_service import get_agent_llm,get_final_llm
from services.research_executor import execute_research_questions
from services.research_report_schema import ResearchReport,ResearchAnalysis
from langchain_core.messages import AIMessage
import json


def generate_answer(state:AgentState):
    answer = generate_response(state['question'])
    return {'answer':answer}



def call_llm(state: AgentState):
    llm = get_agent_llm()
    

    research_questions = state.get("research_questions", [])

    planning_message = SystemMessage(
        content=(
            "Use these research questions to guide your answer:\n"
            + "\n".join(
                f"- {question}"
                for question in research_questions
            )
        )
    )

    response = llm.invoke(
        [planning_message] + state["messages"]
    )

    return {"messages": [response]}

def should_continue(state: AgentState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"




def generate_final_answer(state: AgentState):
    llm = get_final_llm().with_structured_output(
        ResearchReport,
        method="json_mode",
    )
    agent_trace = state.get("agent_trace", [])

    user_question = state["messages"][0].content
    research_results = state.get("research_results", [])
    analysis = state.get("analysis")

    successful_results = [
        item for item in research_results
        if item.get("status") == "SUCCESS"
        and item.get("result", "").strip()
    ]

    evidence = "\n\n".join(
        f"Research question: {item['question']}\n"
        f"Evidence and source URLs:\n{item['result']}"
        for item in successful_results
    )

    failed_questions = [
        f"{item['question']}: {item.get('status', 'UNKNOWN')}"
        for item in research_results
        if item.get("status") != "SUCCESS"
    ]

    if analysis:
            analysis_context = f"""
        Analyst findings:
        Main insights:
        {analysis.main_insights}

        Cross-source agreements:
        {analysis.cross_source_agreements}

        Contradictions:
        {analysis.contradictions}

        Evidence gaps:
        {analysis.evidence_gaps}
        """
    else:
            analysis_context = "No structured analyst output is available."

    prompt = f"""

        
       

        You are the Report Writer Agent in a research system.


        

        User's original request:
        {user_question}

        

        Research evidence:
        {evidence or "No usable research evidence was collected."}

        {analysis_context}

        Requirements:

            1.Use the Analyst's insights where supported by the research evidence.
            2.Preserve meaningful contradictions and limitations.
            3.Do not turn unsupported analyst claims into facts.
            4.Generate source URLs only from the supplied research results.

        Questions with missing or failed research:
        {json.dumps(failed_questions, ensure_ascii=False)}

        Produce a structured research report.

        Rules:
        1. Base factual findings only on the supplied evidence.
        2. Do not invent facts, statistics, quotations, or source URLs.
        3. Include only URLs present in the supplied evidence.
        4. Mention important evidence gaps and failed searches in limitations.
        5. If evidence is insufficient, say so clearly rather than guessing.
        6. Write a concise executive summary that answers the original request.

        Return a JSON object with exactly these fields:
        - executive_summary: string
        - key_findings: array of strings
        - sources: array of strings
        - limitations: array of strings

        Do not include Markdown fences or text outside the JSON object.
        """

    report = llm.invoke(prompt)

    if not report.executive_summary.strip():
        raise ValueError("Research report has an empty executive summary.")

    if not report.key_findings:
        raise ValueError("Research report has no key findings.")

    agent_trace = agent_trace + [{
    "agent": "report_writer",
    "status": "SUCCESS",
    "details": (
        f"Generated report with {len(report.key_findings)} key findings "
        f"using {len(successful_results)} successful research results"
    ),
        }]

    return {
        "report": report,
        "agent_trace": agent_trace,
    }





def plan_research(state: AgentState):
    agent_trace = state.get("agent_trace", [])
    llm = get_final_llm()

    question = state["messages"][0].content

    prompt = f"""
            You are the Planner Agent in a multi-agent research system.

            Your responsibility is to create a research plan, not to answer
            the user's question.

            Analyze the user's request and generate 3 to 5 research questions.

            Rules:
            1. Each question must investigate a distinct aspect of the request.
            2. Avoid duplicate questions and overlapping topics.
            3. Make each question specific enough to guide a web search.
            4. Prioritize the most important aspects of the user's request.
            5. Include relevant context such as geography, industry, or time
            period when specified by the user.
            6. Do not invent assumptions or change the user's intent.
            7. Do not answer the questions.

            Return only a valid JSON array of strings.
            Do not include Markdown fences or explanations.

            Example:
            User question: Research the teaching sector in India

            Output:
            [
            "What is the current structure of India's teaching and education sector?",
            "What are the major challenges faced by teachers and educational institutions in India?",
            "How is technology changing teaching and learning in India?",
            "What are the recent government initiatives affecting teachers and education?",
            "What are the major employment and career opportunities for teachers in India?"
            ]

            User request:
            {question}
            """

    response = llm.invoke(prompt)
    research_questions = json.loads(response.content)

    if not isinstance(research_questions, list):
        raise ValueError("Planner must return a JSON array.")

    if not 3 <= len(research_questions) <= 5:
        raise ValueError("Planner must generate 3 to 5 questions.")

    if not all(
        isinstance(item, str) and item.strip()
        for item in research_questions
    ):
        raise ValueError("Every research question must be a non-empty string.")

    research_questions = [
        item.strip() for item in research_questions
    ]

    agent_trace = agent_trace + [{
    "agent": "planner",
    "status": "SUCCESS",
    "details": f"Generated {len(research_questions)} research questions",
    }]

    return {
    "research_questions": research_questions,
    "agent_trace": agent_trace,
}
    


def execute_research(state: AgentState):
    agent_trace = state.get("agent_trace", [])
    questions = state.get("research_questions", [])
    existing_results = state.get("research_results", [])

    if len(questions) < 3:
        raise ValueError("Research plan must contain at least 3 questions.")

    # Identify questions that have not been researched yet.
    already_researched = {
        item["question"] for item in existing_results
    }

    pending_questions = [
        question
        for question in questions
        if question not in already_researched
    ]

    # Search only new questions.
    new_results = execute_research_questions(pending_questions)

    if len(new_results) != len(pending_questions):
        raise ValueError("Research result count does not match pending questions.")

    # Preserve evidence from previous research passes.
    combined_results = existing_results + new_results
    failed_count = sum(
        1 for item in new_results
        if item.get("status") in ("FAILED", "NO_RESULTS")
    )
    successful_count = sum(
        1 for item in new_results
        if item.get("status") == "SUCCESS"
        and item.get("result", "").strip()
    )
    agent_trace = agent_trace + [{
    "agent": "researcher",
    "status": "SUCCESS" if failed_count == 0 else "PARTIAL",
    "details": (
        f"Researched {len(pending_questions)} new questions; "
            f"{successful_count} successful; "

        f"{failed_count} failed or returned no results; "
        f"{len(combined_results)} total results retained"
    ),
    }]
    
    return {
        "research_results": combined_results,
        "agent_trace": agent_trace,
    }




def analyze_research(state: AgentState):
    research_results = state.get("research_results", [])

    successful_results = [
        item for item in research_results
        if item.get("status") == "SUCCESS"
        and item.get("result", "").strip()
    ]

    if not successful_results:
        raise ValueError(
            "Cannot analyze research because no usable evidence exists."
        )

    evidence = "\n\n".join(
        f"Research question: {item['question']}\n"
        f"Evidence and source URLs:\n{item['result']}"
        for item in successful_results
    )

    llm = get_final_llm().with_structured_output(ResearchAnalysis)

    prompt = f"""
You are the Analyst Agent in a research workflow.

Analyze only the supplied research evidence.

Requirements:
- Extract important insights supported by the evidence.
- Identify conclusions supported by multiple sources.
- Identify contradictions between sources.
- Identify unanswered questions and evidence gaps.
- Do not invent facts, citations, or sources.
- If there is not enough evidence for a conclusion, state that clearly.

Return the required ResearchAnalysis structure.

Research evidence:
{evidence}
"""

    analysis = llm.invoke(prompt)
    agent_trace = list(state.get("agent_trace", []))
    agent_trace.append({
        "agent": "analyst",
        "status": "SUCCESS",
        "details": (
            f"Identified {len(analysis.main_insights)} main insights, "
            f"{len(analysis.contradictions)} contradictions, and "
            f"{len(analysis.evidence_gaps)} evidence gaps"
        ),
    })

    return {
    "analysis": analysis,
    "agent_trace": agent_trace,
}


def check_research_quality(state: AgentState):
    research_results = state.get("research_results", [])
    questions = state.get("research_questions", [])

    successful_results = [
        item for item in research_results
        if item.get("status") == "SUCCESS"
        and item.get("result", "").strip()
    ]

    successful_questions = {
        item["question"] for item in successful_results
    }

    missing_questions = [
        question
        for question in questions
        if question not in successful_questions
    ]

    total_questions = len(questions)
    successful_count = len(successful_questions)

    required_count = max(2, (total_questions + 1) // 2)
    sufficient = successful_count >= required_count

    if sufficient:
        feedback = "Evidence coverage is sufficient."
    else:
        feedback = (
            "Research evidence is insufficient. Investigate these gaps: "
            + "; ".join(missing_questions)
        )

    
    agent_trace = state.get("agent_trace", [])

    agent_trace = agent_trace + [{
        "agent": "quality_checker",
        "status": "SUCCESS" if sufficient else "INSUFFICIENT_EVIDENCE",
        "details": (
            f"Evidence coverage: "
            f"{len(successful_questions)}/{total_questions}; "
            f"sufficient={sufficient}"
        ),
    }]
    

    return {
        "quality_check": {
            "sufficient": sufficient,
            "total_questions": total_questions,
            "successful_questions": successful_count,
            "failed_questions": total_questions - successful_count,
            "required_successful_questions": required_count,
            "reason": feedback,
        },
        "revision_feedback": feedback,
        "agent_trace": agent_trace
    }



def revise_research_plan(state: AgentState):
    llm = get_final_llm()

    original_question = state["messages"][0].content
    existing_questions = state.get("research_questions", [])
    feedback = state.get("revision_feedback", "")

    prompt = f"""
You are the Planner Agent revising a research plan.

Original user request:
{original_question}

Previous research questions:
{json.dumps(existing_questions, ensure_ascii=False)}

Research quality feedback:
{feedback}

Create 2 to 3 NEW research questions that address missing
evidence or under-researched aspects.

Rules:
- Do not repeat existing questions.
- Stay focused on the original user request.
- Make each question specific and suitable for web search.
- Do not answer the questions.
- Return only a valid JSON array of strings.
"""

    response = llm.invoke(prompt)
    new_questions = json.loads(response.content)

    if not isinstance(new_questions, list):
        raise ValueError("Revised plan must be a JSON array.")

    if not 2 <= len(new_questions) <= 3:
        raise ValueError("Revised plan must contain 2 to 3 questions.")

    if not all(
        isinstance(item, str) and item.strip()
        for item in new_questions
    ):
        raise ValueError("Every revised question must be a non-empty string.")

    existing_normalized = {
    question.strip().casefold()
    for question in existing_questions
}

    unique_new_questions = []
    seen = set(existing_normalized)

    for question in new_questions:
        question = question.strip()
        normalized = question.casefold()

        if normalized not in seen:
            unique_new_questions.append(question)
            seen.add(normalized)

    if not unique_new_questions:
        raise ValueError(
            "Planner revision produced no new research questions."
        )

    agent_trace = state.get("agent_trace", [])

    agent_trace = agent_trace + [{
        "agent": "planner",
        "status": "SUCCESS",
        "details": (
            f"Revised research plan with "
            f"{len(unique_new_questions)} new questions"
        ),
    }]

    return {
        "research_questions": existing_questions + unique_new_questions,
        "revision_count": state.get("revision_count", 0) + 1,
        "agent_trace": agent_trace,
    }