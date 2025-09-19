from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.prompts import MessagesPlaceholder
from datetime import datetime
# 加载 .env 文件
load_dotenv()

# ============ 定义工具 ============

def get_current_time(_):
    """获取当前日期时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def web_search(query: str) -> str:
    """执行网络搜索（这里你可以接入实际的搜索API，比如SerpAPI、Bing、DuckDuckGo）"""
    # 这里只是demo，替换成真实搜索逻辑
    return f"搜索结果：模拟搜索到 {query} 的相关新闻..."

def fetch_page(url: str) -> str:
    """抓取网页内容（可用requests/bs4实现，这里只写demo）"""
    return f"模拟抓取 {url} 的网页内容..."

tools = [
    Tool(
        name="get_current_time",
        func=get_current_time,
        description="获取当前时间。当用户请求'最新'、'今天'、'本周'等时间敏感信息时，通常先调用此工具。"
    ),
    Tool(
        name="web_search",
        func=web_search,
        description="用于搜索新闻、赛事、资料等信息，支持任意关键词搜索。"
    ),
    Tool(
        name="fetch_page",
        func=fetch_page,
        description="输入URL，获取网页正文内容。"
    ),
]

# ============ 定义模型 ============

llm = ChatOpenAI(
    model="qwen3-235b-a22b-thinking-2507",
    api_key="sk-c8331ffeed3444cd920ef20888560fcf",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# ============ 定义agent ============
# 需要指定用户调用get_current_time工具获取时间，否则大模型会认为直接使用搜索工具也能获得最新的消息
system_message = """
你是一个信息研究员，负责回答用户的问题。
- 如果用户问“最新/今天/本周/当日”之类的时间敏感问题，可以先调用 get_current_time 确定日期，再结合 web_search。
- 如果问题不需要时间信息，可以直接用 web_search。
- fetch_page 用于在已知URL时获取网页详情。
- 回答时要基于工具结果，避免主观推测。
"""

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    agent_kwargs={
        # "extra_prompt_messages": [MessagesPlaceholder(variable_name="memory")],
        "system_message": system_message,
    },
)

# ============ 测试调用 ============

result = agent.run({
    "input": "帮我查一下LPL最新赛况",
    "chat_history": []   # 第一次对话时传空列表即可
})
print("最终答案：", result)
