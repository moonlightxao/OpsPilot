# -*- coding: utf-8 -*-
"""
Renderer Protocol Interface
Word 渲染器抽象接口

基于 Python Protocol (PEP 544) 定义，用于：
1. 类型检查时的静态分析
2. 模块解耦和依赖注入
3. 文档化模块间的契约
"""

from typing import Protocol, Dict, Any


class IRenderer(Protocol):
    """
    Word 渲染器接口

    职责：
    - 基于 docxtpl 模板引擎渲染 Word 文档
    - 支持 Jinja2 循环和条件语法
    - 支持多种渲染策略：AUTO、TEMPLATE、BUILTIN
    """

    def render(
        self,
        report: Dict[str, Any],
        template_path: str,
        output_path: str
    ) -> str:
        """
        渲染 Word 文档

        Args:
            report: 符合 report_schema.md 规范的字典数据
            template_path: 模板文件路径（.docx）
            output_path: 输出文件路径

        Returns:
            实际输出的文件路径

        Raises:
            TemplateNotFoundError: 模板文件不存在
            TemplateRendererError: 模板渲染失败
        """
        ...
