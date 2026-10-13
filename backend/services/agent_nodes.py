from .agent_state import AgentState
from langchain_core.messages import SystemMessage
from .llm_service import generate_response
from services.llm_service import get_agent_llm,get_final_llm
from services.research_executor import execute_research_questions
from services.research_report_schema import ResearchReport
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
                                method="json_mode")

    user_question = state["messages"][0].content
    research_results = state.get("research_results", [])

    evidence = "\n\n".join(
        f"Research question: {item['question']}\n"
        f"Search results:\n{item['result']}"
        for item in research_results
    )

    prompt = f"""
            You are a research analyst.

            Answer the user's question using the research evidence provided below.

            User question:
            {user_question}

            Research evidence:
            {evidence}

            Requirements:
            - Synthesize the evidence into a coherent answer.
            - Organize the answer with useful headings.
            - Cite source URLs inline when they are available in the evidence.
            - Distinguish supported findings from uncertainty.
            - Do not invent sources or claim that a fact was verified if the evidence
            does not support it.

            Required report structure:

                    1. Executive Summary
                    2. Key Findings
                    3. Sources
                    4. Limitations and Uncertainties

                    Use Markdown headings.
                    List source URLs that support the findings.
                    Do not invent sources.
                    Clearly identify any claims that the provided evidence does not establish.
            Return a valid JSON object with exactly these fields:
                - executive_summary: string
                - key_findings: array of strings
                - sources: array of strings
                - limitations: array of strings

            Do not include Markdown fences or text outside the JSON object.  
            
                  
            """

    # response = llm.invoke(prompt)
    

    # return {"messages": [response]}
    report = llm.invoke(prompt)

    if not report.executive_summary.strip():
        raise ValueError("Research report has an empty executive summary.")

    if not report.key_findings:
        raise ValueError("Research report has no key findings.")

    return {"report": report}



def plan_research(state: AgentState):
    llm = get_final_llm()

    question = state["messages"][0].content

    prompt = f"""
            You are a research planning assistant.

            Break the user's question into 3 to 5 focused research questions.
            Each question should investigate a different aspect of the original question.

            Return only a valid JSON array of strings.
            Do not include Markdown or explanations.

            User question:
            {question}
            """

    response = llm.invoke(prompt)
    research_questions = json.loads(response.content)

    return {
        "research_questions": research_questions
    }


def execute_research(state: AgentState):
    questions = state["research_questions"]

    # Validate the planner output.
    if len(questions) < 3:
        raise ValueError(
            "Research planner must generate at least 3 questions."
        )

    results = execute_research_questions(questions)

    # Validate the number of results.
    if len(results) != len(questions):
        raise ValueError(
            f"Expected {len(questions)} research results, "
            f"but received {len(results)}."
        )

    # Validate that useful evidence was returned.
    usable_results = [
        item for item in results
        if item.get("result")
        and item["result"].strip()
        and item["result"] != "No search results found."
    ]

    if not usable_results:
        raise ValueError(
            "Research failed: no usable evidence was found."
        )

    return {
        "research_results": results
    }
