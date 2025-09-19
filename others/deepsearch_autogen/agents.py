from typing import Dict, Any, List

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from . import prompts
from .search import web_search, fetch_page, get_current_time


def _build_llm_config(config_list: List[Dict[str, Any]], temperature: float = 0.3, timeout: int = 120) -> Dict[str, Any]:
    return {
        "timeout": timeout,
        "temperature": temperature,
        "config_list": config_list,
    }


def get_simple_research_agent(model_client: OpenAIChatCompletionClient):
    tools = [web_search, fetch_page, get_current_time]
    researcher = AssistantAgent(
        name="Researcher",
        model_client=model_client,
        tools=tools,
        system_message=prompts.RESEARCHER_SIMPLE_SYSTEM,
        description="Researcher：使用工具进行网络搜索、查找来源、抽取文本、引用相关片段并附上 URL，每个来源提供简短总结。避免推测。"
    )
    return researcher


def build_agents(model_client: OpenAIChatCompletionClient) -> Dict[str, Any]:

    tools = [web_search, fetch_page, get_current_time]

    planner = AssistantAgent(
        name="Planner",
        model_client=model_client,
        system_message=prompts.PLANNER_SYSTEM,
        description="Planner：拆解问题、分配子任务、控制节奏。"
    )

    researcher = AssistantAgent(
        name="Researcher",
        model_client=model_client,
        tools=tools,
        system_message=prompts.RESEARCHER_SYSTEM,
        description="Researcher：使用工具进行网络搜索、查找来源、抽取文本、引用相关片段并附上 URL，每个来源提供简短总结。避免推测。"
    )

    analyst = AssistantAgent(
        name="Analyst",
        model_client=model_client,
        system_message=prompts.ANALYST_SYSTEM,
        description="Analyst：整合收集到的证据，按主题聚类，并记录一致点、分歧和空白点。如有需要，提出进一步证据收集的建议。引用保持行内格式，如 [1]、[2]。"
    )

    critic = AssistantAgent(
        name="Critic",
        model_client=model_client,
        system_message=prompts.CRITIC_SYSTEM,
        description="识别风险，并提出修正或额外验证步骤，指明具体来源以进行验证。"
    )

    synthesizer = AssistantAgent(
        name="Synthesizer",
        model_client=model_client,
        system_message=prompts.SYNTHESIZER_SYSTEM,
        description="生成最终的、结构清晰的回答，优化可读性和实用性。"
    )

    agents = {
        "planner": planner,
        "researcher": researcher,
        "analyst": analyst,
        "critic": critic,
        "synthesizer": synthesizer,
    }
    return agents


