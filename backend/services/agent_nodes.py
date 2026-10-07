from .agent_state import AgentState
from .llm_service import generate_response
from services.llm_service import get_agent_llm,get_final_llm



def generate_answer(state:AgentState):
    answer = generate_response(state['question'])
    return {'answer':answer}



def call_llm(state: AgentState):
    print("\n===== LLM INPUT =====")

    for message in state["messages"]:
        print(type(message).__name__)
        print("content:", message.content)
        print("tool_calls:", getattr(message, "tool_calls", None))

    print("=====================")

    llm = get_agent_llm()
    response = llm.invoke(state["messages"])

    print("\n===== LLM OUTPUT =====")
    print("content:", response.content)
    print("tool_calls:", response.tool_calls)
    print("======================")

    return {
        "messages": [response]
    }

def should_continue(state: AgentState):
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"


def generate_final_answer(state: AgentState):
    llm = get_final_llm()

    user_question = state["messages"][0].content
    tool_result = state["messages"][-1].content

    prompt = f"""
Answer the user's question using the research result below.

User question:
{user_question}

Research result:
{tool_result}

Give a clear and concise final answer.
Do not call any tools.
"""

    response = llm.invoke(prompt)

    return {"messages": [response]}