"""
tools.py
--------
The agent's three tools: calculator, current time, and a fact search over
the local knowledge base (docs/). Same OpenAI-compatible schema Groq uses.
"""

import datetime
from knowledge_base import KnowledgeBase

kb = KnowledgeBase("docs")


def calculator(expression: str) -> str:
    allowed = set("0123456789+-*/(). ")
    if not set(expression) <= allowed:
        return "Error: expression contains disallowed characters."
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"


def get_current_time(timezone: str = "UTC") -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


def search_facts(query: str) -> str:
    """Search the local knowledge base for relevant facts."""
    results = kb.search(query, top_k=2)
    if not results:
        return "No relevant facts found in the knowledge base."
    return "\n\n".join(f"[{r['source']}] {r['text']}" for r in results)


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a basic arithmetic expression, e.g. '12 * (3 + 4)'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "The arithmetic expression to evaluate."}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time (UTC).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_facts",
            "description": "Search a local knowledge base of facts about Claude models and Anthropic API concepts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for."}
                },
                "required": ["query"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "search_facts": search_facts,
}


def run_tool(name: str, tool_input: dict) -> str:
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return f"Error: unknown tool '{name}'"
    return fn(**tool_input)
