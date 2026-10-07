import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from services.tools.capital_tool import get_capital
from services.tools.search_tool import web_search

load_dotenv()

def generate_response(prompt: str) -> str:
        model = ChatGroq(
                    model="openai/gpt-oss-120b", 
                    api_key=os.environ.get("GROQ_API_KEY")
                )    
        answer = model.invoke(prompt).content
        return answer



def get_agent_llm():
    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
    )

    return llm.bind_tools([get_capital,web_search])

def get_final_llm():
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
    )

if __name__ == "__main__":
    result = generate_response("Explain deep learning in simple terms.")
    print(result)