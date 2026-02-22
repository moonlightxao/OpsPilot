# Word Renderer Module
# 负责基于 python-docx 和 docxtpl 的文档渲染

from .word_renderer import WordRenderer, render_report
from .template_renderer import TemplateRenderer, render_with_template

__all__ = [
    'WordRenderer', 
    'render_report',
    'TemplateRenderer',
    'render_with_template'
]
