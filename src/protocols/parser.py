# -*- coding: utf-8 -*-
"""
Parser Protocol Interface
Excel 解析器抽象接口

基于 Python Protocol (PEP 544) 定义，用于：
1. 类型检查时的静态分析
2. 模块解耦和依赖注入
3. 文档化模块间的契约
"""

from typing import Protocol, Dict, Any, List, Optional


class IParser(Protocol):
    """
    Excel 解析器接口

    职责：
    - 读取 Excel 文件
    - 动态表头解析
    - 数据清洗与空值处理
    - 生成符合 report_schema.md 的中间态数据
    - 风险评估（可选）
    """

    def parse(self, excel_path: str) -> Dict[str, Any]:
        """
        解析 Excel 文件，返回 report 数据结构

        Args:
            excel_path: Excel 文件路径

        Returns:
            符合 report_schema.md 规范的字典数据，包含：
            - meta: 元数据（source_file, generated_at, version 等）
            - summary: 摘要信息（total_tasks, total_sheets, high_risk_count 等）
            - has_risk_alerts: 是否存在风险告警
            - risk_alerts: 风险告警列表
            - implementation_summary: 实施总表数据
            - sections: 各章节详细数据
        """
        ...

    def get_sheets(self) -> List[str]:
        """
        获取所有已解析的 Sheet 名称列表

        Returns:
            Sheet 名称列表（按优先级排序）
        """
        ...

    def assess_risks(
        self,
        report: Dict[str, Any],
        use_llm: bool = False
    ) -> Dict[str, Any]:
        """
        对解析结果进行风险评估

        Args:
            report: 解析后的 report 数据
            use_llm: 是否使用 LLM 辅助分析

        Returns:
            更新后的 report，包含：
            - risk_alerts: 风险告警列表
            - risk_summary: 风险摘要统计
        """
        ...
