# -*- coding: utf-8 -*-
"""
摘要生成器模块

职责：
- 从 Excel 数据中提取变更应用名称（规则驱动）
- 使用 LLM 生成变更原因和变更影响（LLM 增强）
- LLM 不可用时自动降级到规则模板

设计原则：
1. 变更应用：精确提取，不允许幻觉
2. 变更原因/影响：LLM 生成自然语言，有兜底模板
"""

import logging
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..llm import BaseLLMClient
from .prompts.summary_generation import (
    DEFAULT_SUMMARY_TEMPLATES,
    SUMMARY_GENERATION_PROMPT,
)

logger = logging.getLogger(__name__)


@dataclass
class SummaryContext:
    """摘要生成的上下文数据"""
    application_names: str
    total_tasks: int
    module_count: int
    high_risk_count: int
    module_summary: str
    action_summary: str
    raw_applications: List[str]


class SummaryGenerator:
    """
    摘要生成器

    策略：
    - application_name：规则驱动，从 Excel 列中提取去重
    - change_reason：LLM 生成，有兜底模板
    - change_impact：LLM 生成，有兜底模板
    """

    def __init__(
        self,
        llm_client: Optional[BaseLLMClient] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化摘要生成器

        Args:
            llm_client: LLM 客户端实例（可选）
            config: summary_extraction 配置节点
        """
        self.llm_client = llm_client
        self.config = config or {}
        self.app_config = self.config.get('application_name', {})
        self.llm_config = self.config.get('llm_summary', {})

    def generate(self, excel_data: Dict[str, Any]) -> Dict[str, str]:
        """
        生成变更摘要

        Args:
            excel_data: 解析后的 Excel 数据，包含 sections, implementation_summary 等

        Returns:
            包含 application_name, change_reason, change_impact 的字典
        """
        # 1. 提取上下文数据
        context = self._extract_context(excel_data)

        # 2. 生成变更原因和变更影响
        if self._should_use_llm():
            llm_result = self._generate_with_llm(context)
        else:
            llm_result = self._generate_with_fallback(context)

        return {
            "application_name": context.application_names,
            "change_reason": llm_result.get("change_reason", ""),
            "change_impact": llm_result.get("change_impact", "")
        }

    def _extract_context(self, excel_data: Dict[str, Any]) -> SummaryContext:
        """
        从 Excel 数据中提取上下文信息

        Args:
            excel_data: 解析后的 Excel 数据

        Returns:
            SummaryContext 上下文对象
        """
        sections = excel_data.get('sections', [])
        implementation_summary = excel_data.get('implementation_summary', {})
        summary = excel_data.get('summary', {})

        # 提取应用名称
        raw_applications = self._extract_applications(sections, implementation_summary)
        application_names = self._join_applications(raw_applications)

        # 统计模块信息
        module_summary = self._build_module_summary(sections)

        # 统计操作类型
        action_summary = self._build_action_summary(sections)

        return SummaryContext(
            application_names=application_names,
            total_tasks=summary.get('total_tasks', 0),
            module_count=len(sections),
            high_risk_count=summary.get('high_risk_count', 0),
            module_summary=module_summary,
            action_summary=action_summary,
            raw_applications=raw_applications
        )

    def _extract_applications(
        self,
        sections: List[Dict[str, Any]],
        implementation_summary: Dict[str, Any]
    ) -> List[str]:
        """
        从各模块中提取应用名称

        提取策略：
        1. 从配置的 source columns 中提取
        2. 去重
        3. 过滤空值

        Args:
            sections: 章节列表
            implementation_summary: 实施总表数据

        Returns:
            应用名称列表（已去重）
        """
        source_columns = self.app_config.get('sources', [])
        dedupe = self.app_config.get('dedupe', True)

        applications = []

        # 从各章节提取
        for section in sections:
            columns = section.get('columns', [])
            action_groups = section.get('action_groups', [])

            # 确定要提取的列
            extract_cols = self._find_extract_columns(columns, source_columns)

            for action_group in action_groups:
                for task in action_group.get('tasks', []):
                    cells = task.get('cells', [])
                    for col_idx, col_name in enumerate(columns):
                        if col_name in extract_cols and col_idx < len(cells):
                            value = cells[col_idx]
                            if value and isinstance(value, str) and value.strip():
                                applications.append(value.strip())

        # 从实施总表提取
        impl_columns = implementation_summary.get('columns', [])
        impl_rows = implementation_summary.get('rows', [])
        extract_cols = self._find_extract_columns(impl_columns, source_columns)

        for row in impl_rows:
            cells = row.get('cells', [])
            for col_idx, col_name in enumerate(impl_columns):
                if col_name in extract_cols and col_idx < len(cells):
                    value = cells[col_idx]
                    if value and isinstance(value, str) and value.strip():
                        applications.append(value.strip())

        # 去重并保持顺序
        if dedupe:
            seen = set()
            unique_apps = []
            for app in applications:
                if app not in seen:
                    seen.add(app)
                    unique_apps.append(app)
            applications = unique_apps

        return applications

    def _find_extract_columns(
        self,
        actual_columns: List[str],
        source_configs: List[Dict[str, str]]
    ) -> List[str]:
        """
        找出实际存在的提取列

        Args:
            actual_columns: 实际列名列表
            source_configs: 配置的源列列表

        Returns:
            实际可提取的列名列表
        """
        extract_cols = []
        for source in source_configs:
            col_name = source.get('column', '')
            if col_name in actual_columns:
                extract_cols.append(col_name)
        return extract_cols

    def _join_applications(self, applications: List[str]) -> str:
        """
        将应用名称列表连接为字符串

        Args:
            applications: 应用名称列表

        Returns:
            连接后的字符串
        """
        if not applications:
            return ""

        join_with = self.app_config.get('join_with', '、')
        return join_with.join(applications)

    def _build_module_summary(self, sections: List[Dict[str, Any]]) -> str:
        """
        构建模块分布摘要

        Args:
            sections: 章节列表

        Returns:
            模块分布文本
        """
        lines = []
        for section in sections:
            name = section.get('section_name', '')
            task_count = section.get('task_count', 0)
            lines.append(f"- {name}: {task_count} 项任务")
        return "\n".join(lines)

    def _build_action_summary(self, sections: List[Dict[str, Any]]) -> str:
        """
        构建操作类型统计摘要

        Args:
            sections: 章节列表

        Returns:
            操作类型统计文本
        """
        action_counter: Counter = Counter()

        for section in sections:
            for action_group in section.get('action_groups', []):
                action_type = action_group.get('action_type', '')
                task_count = action_group.get('task_count', 0)
                action_counter[action_type] += task_count

        lines = []
        for action_type, count in action_counter.most_common(10):
            lines.append(f"- {action_type}: {count} 项")
        return "\n".join(lines)

    def _should_use_llm(self) -> bool:
        """判断是否应使用 LLM"""
        if not self.llm_config.get('enabled', False):
            return False
        if not self.llm_client:
            return False
        return self.llm_client.is_available()

    def _generate_with_llm(self, context: SummaryContext) -> Dict[str, str]:
        """
        使用 LLM 生成摘要

        Args:
            context: 上下文数据

        Returns:
            包含 change_reason 和 change_impact 的字典
        """
        user_prompt = SUMMARY_GENERATION_PROMPT["user_template"].format(
            application_names=context.application_names or "（未知）",
            total_tasks=context.total_tasks,
            module_count=context.module_count,
            high_risk_count=context.high_risk_count,
            module_summary=context.module_summary or "（无模块信息）",
            action_summary=context.action_summary or "（无操作类型统计）"
        )

        try:
            response = self.llm_client.chat(
                system_prompt=SUMMARY_GENERATION_PROMPT["system"],
                user_prompt=user_prompt,
                max_tokens=self.llm_config.get('max_tokens', 500),
                temperature=self.llm_config.get('temperature', 0.3)
            )

            return self._parse_llm_response(response.content, context)

        except Exception as e:
            logger.warning(f"LLM 生成摘要失败，使用兜底模板: {e}")
            return self._generate_with_fallback(context)

    def _parse_llm_response(
        self,
        content: str,
        context: SummaryContext
    ) -> Dict[str, str]:
        """
        解析 LLM 响应

        Args:
            content: LLM 返回的内容
            context: 上下文数据（用于兜底）

        Returns:
            解析后的字典
        """
        import json
        import re

        json_str = None

        # 策略 1: 提取 ```json 代码块
        json_block_match = re.search(
            r'```json\s*\n?(.*?)\n?```',
            content,
            re.DOTALL | re.IGNORECASE
        )
        if json_block_match:
            json_str = json_block_match.group(1).strip()

        # 策略 2: 提取任意 JSON 对象
        if not json_str:
            json_object_match = re.search(
                r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',
                content,
                re.DOTALL
            )
            if json_object_match:
                json_str = json_object_match.group(0).strip()

        # 尝试解析 JSON
        if json_str:
            try:
                result = json.loads(json_str)
                return {
                    "change_reason": result.get("change_reason", ""),
                    "change_impact": result.get("change_impact", "")
                }
            except json.JSONDecodeError as e:
                logger.warning(f"JSON 解析失败: {e}")

        # 解析失败，使用兜底
        return self._generate_with_fallback(context)

    def _generate_with_fallback(self, context: SummaryContext) -> Dict[str, str]:
        """
        使用兜底模板生成摘要

        Args:
            context: 上下文数据

        Returns:
            包含 change_reason 和 change_impact 的字典
        """
        fallback = self.llm_config.get('fallback_template', DEFAULT_SUMMARY_TEMPLATES)

        change_reason_template = fallback.get(
            'change_reason',
            DEFAULT_SUMMARY_TEMPLATES['change_reason']
        )
        change_impact_template = fallback.get(
            'change_impact',
            DEFAULT_SUMMARY_TEMPLATES['change_impact']
        )

        # 准备模板变量
        template_vars = {
            'total_tasks': context.total_tasks,
            'app_count': len(context.raw_applications),
            'applications': context.application_names,
            'module_count': context.module_count,
            'high_risk_count': context.high_risk_count
        }

        try:
            change_reason = change_reason_template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"模板变量缺失: {e}")
            change_reason = change_reason_template.split('{')[0]

        try:
            change_impact = change_impact_template.format(**template_vars)
        except KeyError as e:
            logger.warning(f"模板变量缺失: {e}")
            change_impact = change_impact_template.split('{')[0]

        return {
            "change_reason": change_reason,
            "change_impact": change_impact
        }
