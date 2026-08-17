from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from app.graph.state import WeatherState
from app.graph.nodes import llm_node, should_continue
from app.llm import ALL_TOOLS

# Initialize State Graph
builder = StateGraph(WeatherState)

# Add Nodes
builder.add_node("llm", llm_node)
builder.add_node("tools", ToolNode(ALL_TOOLS))

# Connect Edges
builder.add_edge(START, "llm")
builder.add_conditional_edges(
    "llm",
    should_continue,
    {
        "tools": "tools",
        "end": END
    }
)
builder.add_edge("tools", "llm")

# In-memory checkpointer preserves conversation threads per thread_id (session_id)
checkpointer = MemorySaver()
workflow = builder.compile(checkpointer=checkpointer)