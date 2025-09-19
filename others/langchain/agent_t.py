import datetime

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.tools import StructuredTool
import os

# 加载 .env 文件
load_dotenv()

from langchain_tavily import TavilySearch
from langchain.chat_models import init_chat_model

search = TavilySearch(max_results=2)
# search_results = search.invoke("What is the weather in SF")
# print(search_results)
# If we want, we can create other tools.
# Once we have all the tools we want, we can put them in a list that we will reference later.
tools = [search]


model = init_chat_model(
  "qwen3-235b-a22b-thinking-2507", model_provider="openai",
  api_key="sk-c8331ffeed3444cd920ef20888560fcf",
  base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

model_with_tools = model.bind_tools(tools)

# query = "Search for the weather in SF"
# response = model_with_tools.invoke([{"role": "user", "content": query}])
#
# print(f"Message content: {response.text()}\n")
# print(f"Tool calls: {response.tool_calls}")

@tool
def get_current_time() -> str:
    """
    获取当前时间：当用户问到模糊时间的时候，通过此工具获取当前时间来判断用户所问的具体时间是什么时候
    """
    return str(datetime.datetime.now())

@tool
def web_search(query: str) -> str:
    """
    联网搜索相关内容并返回
    """
    return "LPL天下第一"


from langgraph.prebuilt import create_react_agent

agent_executor = create_react_agent(model, [web_search, get_current_time])
input_message = {"role": "user", "content": "搜索LPL最新咨询"}
response = agent_executor.invoke({"messages": [input_message]})

for message in response["messages"]:
    message.pretty_print()