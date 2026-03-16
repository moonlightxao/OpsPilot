# -*- coding: utf-8 -*-
"""
OpsPilot Protocol Interfaces
模块间的抽象接口定义

基于 Python Protocol (PEP 544) 定义，用于：
1. 类型检查时的静态分析
2. 模块解耦和依赖注入
3. 文档化模块间的契约

使用示例:
    from src.protocols import IParser, IRenderer, ILLMClient

    def process_excel(parser: IParser, renderer: IRenderer) -> None:
        report = parser.parse("input.xlsx")
        renderer.render(report, "template.docx", "output.docx")
"""

from .parser import IParser
from .renderer import IRenderer
from .llm import ILLMClient

__all__ = [
    "IParser",
    "IRenderer",
    "ILLMClient",
]
