from langchain_groq import ChatGroq
from agent_tools import get_capital
from agent_graph import tool_node
from dotenv import load_dotenv
load_dotenv()
import os 

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.environ.get("GROQ_API_KEY"),
    temperature=0
)

llm_with_tools = llm.bind_tools([get_capital])

response = llm_with_tools.invoke(
    "Use the get_capital tool to find the capital of India?"
)

tool_result = tool_node.invoke({
    "messages": [
        response
    ]
})

print(tool_result)
print(response.tool_calls)