from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """统一的 LLM 响应结构"""
    content: str
    model: str
    usage: dict  # {"prompt_tokens": int, "completion_tokens": int}
    raw_response: Optional[dict] = None


class BaseLLMClient(ABC):
    """LLM 客户端抽象基类"""

    def __init__(self, model: str, **kwargs):
        self.model = model
        self.config = kwargs

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str, **kwargs) -> LLMResponse:
        """发送聊天请求"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查客户端是否可用"""
        pass

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {"provider": self.__class__.__name__, "model": self.model}
