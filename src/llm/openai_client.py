"""OpenAI API 客户端"""

import os
from typing import Optional
from .base import BaseLLMClient, LLMResponse


class OpenAIClient(BaseLLMClient):
    """OpenAI API 客户端"""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")

        from openai import OpenAI
        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> LLMResponse:
        """发送聊天请求"""
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=kwargs.get("max_tokens", 500),
            temperature=kwargs.get("temperature", 0.1)
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            },
            raw_response=response.model_dump()
        )

    def is_available(self) -> bool:
        """检查客户端是否可用"""
        return bool(self.api_key)
