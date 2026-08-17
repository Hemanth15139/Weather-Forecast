from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from app.graph.state import WeatherState
from app.graph.nodes import llm_node, should_continue
from app.tools import get_weather, get_historical_weather

builder= StateGraph(WeatherState)

builder.add_node(
    'llm',
    llm_node
)

builder.add_node(
    'tools',
    ToolNode([get_weather, get_historical_weather])
)

builder.add_edge(
    START,
    'llm'
)


builder.add_conditional_edges(
    'llm',
    should_continue,
    {
        "tools":"tools",
        "end":END
    },
)

# builder.add_edge(
#     'llm',
#     END
# )

builder.add_edge(
    'tools',
    'llm'
)

from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
workflow = builder.compile(checkpointer=checkpointer)