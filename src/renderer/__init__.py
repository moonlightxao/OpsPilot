# Renderer Module
# 负责基于 docxtpl 模板填充或 python-docx 内置渲染的 Word 文档生成

from .template_renderer import TemplateRenderer, render_with_template

__all__ = [
    'TemplateRenderer',
    'render_with_template'
]
