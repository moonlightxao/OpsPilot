from .base import BaseLLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .ollama_client import OllamaClient


def create_llm_client(config: dict) -> BaseLLMClient:
    """根据配置创建 LLM 客户端"""
    provider = config.get("provider", "ollama").lower()
    model = config.get("model")

    if provider == "openai":
        return OpenAIClient(
            model=model or "gpt-4o-mini",
            api_key=config.get("api_key"),
            base_url=config.get("base_url")
        )
    elif provider == "anthropic":
        return AnthropicClient(
            model=model or "claude-sonnet-4-6",
            api_key=config.get("api_key")
        )
    elif provider == "ollama":
        return OllamaClient(
            model=model or "qwen2.5:7b",
            base_url=config.get("base_url")
        )
    else:
        raise ValueError(f"不支持的 LLM 提供方: {provider}")
