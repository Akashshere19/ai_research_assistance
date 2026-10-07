from langchain_core.tools import tool


@tool
def get_capital(country: str) -> str:
    """Return the capital city of a country."""
    
    capitals = {
        "india": "New Delhi",
        "china": "Beijing",
        "japan": "Tokyo",
        "france": "Paris",
        "germany": "Berlin",
    }

    return capitals.get(
        country.lower(),
        "I don't know the capital of that country."
    )