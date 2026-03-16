# -*- coding: utf-8 -*-
"""
LLM Client Protocol Interface
LLM 客户端抽象接口

基于 Python Protocol (PEP 544) 定义，用于：
1. 类型检查时的静态分析
2. 模块解耦和依赖注入
3. 文档化模块间的契约

与现有 BaseLLMClient 保持一致的方法签名
"""

from dataclasses import dataclass
from typing import Protocol, Optional, Any


@dataclass
class LLMResponse:
    """
    统一的 LLM 响应结构（Protocol 层独立定义，避免循环依赖）
    """
    content: str
    model: str
    usage: dict  # {"prompt_tokens": int, "completion_tokens": int}
    raw_response: Optional[dict] = None


class ILLMClient(Protocol):
    """
    LLM 客户端接口

    职责：
    - 与大语言模型 API 通信
    - 提供统一的聊天接口
    - 处理响应和错误
    """

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> LLMResponse:
        """
        发送聊天请求

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            **kwargs: 额外参数（temperature, max_tokens 等）

        Returns:
            LLMResponse 包含：
            - content: 响应内容
            - model: 使用的模型名称
            - usage: token 使用统计
            - raw_response: 原始响应数据
        """
        ...

    def is_available(self) -> bool:
        """
        检查客户端是否可用

        Returns:
            客户端是否可以正常工作
        """
        ...

    def get_model_info(self) -> dict:
        """
        获取模型信息

        Returns:
            包含 provider 和 model 名称的字典
        """
        ...
