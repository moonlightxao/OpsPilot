"""LLM 风险分析器"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import json
import re
import logging

from ..llm import BaseLLMClient
from .prompts.risk_assessment import RISK_ASSESSMENT_PROMPT, SCENARIO_ENHANCEMENTS

logger = logging.getLogger(__name__)


@dataclass
class OperationContext:
    """结构化操作上下文，供 LLM 分析"""
    sheet_name: str
    action_type: str
    instruction: str
    sample_tasks: List[Dict[str, Any]]


class LLMRiskAnalyzer:
    """LLM 风险分析器 - 支持多种 LLM 后端"""

    def __init__(self, llm_client: BaseLLMClient):
        """
        初始化 LLM 风险分析器

        Args:
            llm_client: LLM 客户端实例
        """
        self.llm_client = llm_client
        self.system_prompt = RISK_ASSESSMENT_PROMPT["system"]
        self.user_template = RISK_ASSESSMENT_PROMPT["user_template"]

    def analyze(self, context: OperationContext) -> Dict[str, Any]:
        """
        调用 LLM 分析风险

        Args:
            context: 操作上下文

        Returns:
            风险评估结果字典
        """
        tasks_text = self._format_tasks(context.sample_tasks)

        user_prompt = self.user_template.format(
            sheet_name=context.sheet_name,
            action_type=context.action_type,
            instruction=context.instruction or "（无操作说明）",
            sample_tasks=tasks_text
        )

        # 添加场景增强
        enhancements = self._detect_scenarios(context)
        if enhancements:
            user_prompt += "\n\n" + "\n".join(enhancements)

        # 使用统一接口调用
        response = self.llm_client.chat(
            system_prompt=self.system_prompt,
            user_prompt=user_prompt,
            max_tokens=500,
            temperature=0.1
        )

        return self._parse_response(response.content)

    def _format_tasks(self, tasks: List[Dict[str, Any]]) -> str:
        """格式化任务数据"""
        if not tasks:
            return "（无任务数据）"

        lines = []
        for i, task in enumerate(tasks[:5], 1):
            cells = task.get("cells", [])
            line = f"{i}. {' | '.join(str(c) for c in cells if c)}"
            lines.append(line)

        return "\n".join(lines)

    def _detect_scenarios(self, context: OperationContext) -> List[str]:
        """检测特殊场景"""
        enhancements = []
        text = f"{context.sheet_name} {context.action_type} {context.instruction}".lower()

        for key, enhancement in SCENARIO_ENHANCEMENTS.items():
            if key == "production" and ("生产" in text or "prod" in text):
                enhancements.append(enhancement)
            elif key == "database" and ("数据库" in text or "database" in text or "db" in text):
                enhancements.append(enhancement)
            elif key == "batch" and ("批量" in text or "batch" in text):
                enhancements.append(enhancement)

        return enhancements

    def _parse_response(self, content: str) -> Dict[str, Any]:
        """解析 LLM 响应，支持多种 JSON 提取策略"""
        json_str = None

        # 策略 1: 提取 ```json 代码块
        json_block_match = re.search(
            r'```json\s*\n?(.*?)\n?```',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if json_block_match:
            json_str = json_block_match.group(1).strip()
            logger.debug("使用 ```json 代码块提取策略")

        # 策略 2: 提取任意 ``` 代码块
        if not json_str:
            code_block_match = re.search(
                r'```\s*\n?(.*?)\n?```',
                content,
                re.DOTALL
            )
            if code_block_match:
                block_content = code_block_match.group(1).strip()
                # 检查是否像 JSON
                if block_content.startswith('{') and block_content.endswith('}'):
                    json_str = block_content
                    logger.debug("使用通用代码块提取策略")

        # 策略 3: 使用正则提取最外层 JSON 对象
        if not json_str:
            json_object_match = re.search(
                r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
                content,
                re.DOTALL
            )
            if json_object_match:
                json_str = json_object_match.group(0).strip()
                logger.debug("使用正则 JSON 对象提取策略")

        # 策略 4: 直接使用原始内容
        if not json_str:
            json_str = content.strip()
            logger.debug("使用原始内容策略")

        # 尝试解析 JSON
        try:
            result = json.loads(json_str)

            # 确保必要字段存在
            return {
                "risk_level": result.get("risk_level", "unknown"),
                "risk_score": result.get("risk_score", 0),
                "risk_reasons": result.get("risk_reasons", []),
                "suggestions": result.get("suggestions", []),
                "raw_response": content
            }
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}, 内容预览: {json_str[:100]}...")
            return {
                "risk_level": "unknown",
                "risk_score": 0,
                "risk_reasons": [{"reason": f"JSON 解析失败: {str(e)}", "severity": "error"}],
                "raw_response": content
            }
        except Exception as e:
            logger.error(f"解析响应时发生未知错误: {e}")
            return {
                "risk_level": "unknown",
                "risk_score": 0,
                "risk_reasons": [{"reason": f"解析失败: {str(e)}", "severity": "error"}],
                "raw_response": content
            }
