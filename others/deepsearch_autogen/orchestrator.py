from typing import Dict, Any, List, Optional

from autogen_agentchat.teams import SelectorGroupChat
from autogen_core.models import ModelInfo, ModelFamily
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.ui import Console

import asyncio

from others.deepsearch_autogen.agents import build_agents


def _default_model_list(model: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Build a default config_list for AutoGen. Supports OpenAI and Azure OpenAI via env vars.
    """
    model_name = model or "gpt-4o-mini"
    # AutoGen reads provider from keys present; keep minimal here.
    return [
        {
            "model": model_name,
            "api_key": None,  # Read from env inside AutoGen/OpenAI libs
        }
    ]

SELECT_PROMPT = """选择一个智能体来执行任务。

{roles}

当前对话上下文：
{history}

阅读以上对话，然后从 {participants} 中选择一个智能体来执行下一个任务。
确保在其他智能体开始工作之前，Planner 智能体已经分配好任务。
只能选择一个智能体。

"""


def run_deepsearch(
    task: str,
    *,
    model: Optional[str] = None,
    max_rounds: int = 12,
    summary_only: bool = True,
) -> Dict[str, Any]:
    model_client = OpenAIChatCompletionClient(
        model="qwen3-235b-a22b-instruct-2507",
        api_key="sk-c8331ffeed3444cd920ef20888560fcf",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model_info=ModelInfo(
            vision=False, function_calling=True, json_output=True, structured_output=True, family=ModelFamily.ANY
        )
    )

    config_list = _default_model_list(model)
    agents = build_agents(config_list, model_client)
    text_mention_termination = TextMentionTermination("TERMINATE")
    max_messages_termination = MaxMessageTermination(max_messages=max_rounds)
    termination = text_mention_termination | max_messages_termination
    team = SelectorGroupChat(
        list(agents.values()),
        model_client=model_client,
        termination_condition=termination,
        selector_prompt=SELECT_PROMPT,
        allow_repeated_speaker=True,  # Allow an agent to speak multiple turns in a row.
    )

    asyncio.run(Console(team.run_stream(task=task)))


if __name__ == '__main__':
    # """python -m others.deepsearch_autogen.main "RAG 检索增强生成的评测指标有哪些？各自优缺点？" --rounds 10 --full"""
    run_deepsearch("RAG 检索增强生成的评测指标有哪些？各自优缺点？")

