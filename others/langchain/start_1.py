import getpass
import os

# if not os.environ.get("OPENAI_API_KEY"):
#     os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")

from langchain.chat_models import init_chat_model

model = init_chat_model(
  "qwen3-235b-a22b-thinking-2507", model_provider="openai",
  api_key="sk-c8331ffeed3444cd920ef20888560fcf",
  base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

print(model.invoke("Hello"))
