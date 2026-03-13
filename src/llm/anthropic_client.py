"""Anthropic API 客户端"""

import os
from typing import Optional
from .base import BaseLLMClient, LLMResponse


class AnthropicClient(BaseLLMClient):
    """Anthropic API 客户端"""

    def __init__(
        self,
        model: str = "claude-sonnet-4-6-20250514",
        api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        import anthropic
        self._client = anthropic.Anthropic(api_key=self.api_key)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        response = self._client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 500),
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )

        return LLMResponse(
            content=response.content[0].text,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens
            },
            raw_response=response.model_dump()
        )

    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return bool(self.api_key)
