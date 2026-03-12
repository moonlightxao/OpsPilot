"""Ollama 本地模型客户端"""

import os
import requests
from typing import Optional, List
from .base import BaseLLMClient, LLMResponse


class OllamaClient(BaseLLMClient):
    """Ollama 本地模型客户端"""

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434"
        )

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> LLMResponse:
        """调用 Ollama API"""
        response = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "num_predict": kwargs.get("max_tokens", 500),
                    "temperature": kwargs.get("temperature", 0.1)
                }
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data["message"]["content"],
            model=data.get("model", self.model),
            usage={
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0)
            },
            raw_response=data
        )

    def is_available(self) -> bool:
        """检查 Ollama 服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        """列出可用的本地模型"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return [m["name"] for m in response.json().get("models", [])]
        except Exception:
            pass
        return []
