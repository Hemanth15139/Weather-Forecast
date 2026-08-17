import sys
import os

# Adjust sys.path to allow importing 'app' as a package when running app.py directly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir in sys.path:
    sys.path.remove(current_dir)
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from app.tools import get_weather

from app.graph.workflow import workflow
from langchain_core.messages import HumanMessage

load_dotenv()

# model= ChatGoogleGenerativeAI(

#     model="gemini-3.5-flash",
#     temperature=0,
# )

# llm_tools= model.bind_tools(
#     [get_weather]
# )

# response= llm_tools.invoke(
#     "what is the weather in hyderabad"
# )
# if not response:
#     print("Not a valid response")


# if response.tool_calls:
#     tool_call= response.tool_calls[0]

#     result= get_weather.invoke(
#         tool_call["args"]
#     )



#     print(result)


result= workflow.invoke(
    {
        "messages": [
            HumanMessage(
                content="What is the weather in hyderabad"
            )
        ]
    }
)


for message in result["messages"]:

    print(message)