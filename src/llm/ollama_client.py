"""Ollama 本地模型客户端"""

import os
import time
import logging
import requests
from typing import Optional, List
from .base import BaseLLMClient, LLMResponse

logger = logging.getLogger(__name__)


class OllamaClientError(Exception):
    """Ollama 客户端异常"""
    pass


class OllamaClient(BaseLLMClient):
    """Ollama 本地模型客户端"""

    # 默认重试配置
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_RETRY_DELAY = 1.0
    DEFAULT_TIMEOUT = 60

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        base_url: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        timeout: int = DEFAULT_TIMEOUT,
        **kwargs
    ):
        super().__init__(model, **kwargs)
        self.base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL",
            "http://localhost:11434"
        )
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> LLMResponse:
        """调用 Ollama API，支持自动重试"""
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return self._do_chat(system_prompt, user_prompt, **kwargs)
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.warning(
                    f"Ollama 请求超时 (尝试 {attempt + 1}/{self.max_retries}): {e}"
                )
            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.warning(
                    f"Ollama 连接失败 (尝试 {attempt + 1}/{self.max_retries}): {e}"
                )
            except requests.exceptions.HTTPError as e:
                # 4xx 错误不重试
                if 400 <= e.response.status_code < 500:
                    raise OllamaClientError(f"Ollama 请求错误: {e}") from e
                last_error = e
                logger.warning(
                    f"Ollama HTTP 错误 (尝试 {attempt + 1}/{self.max_retries}): {e}"
                )
            except Exception as e:
                last_error = e
                logger.error(f"Ollama 未知错误: {e}")

            # 等待后重试（最后一次不等待）
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))

        raise OllamaClientError(
            f"Ollama 请求失败，已重试 {self.max_retries} 次: {last_error}"
        ) from last_error

    def _do_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> LLMResponse:
        """执行单次 API 调用"""
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
            timeout=kwargs.get("timeout", self.timeout)
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
