# -*- coding: utf-8 -*-
"""
OpsPilot MCP Server

通过 MCP 协议暴露 OpsPilot 的 Excel 解析与 Word 生成能力。

工具列表:
- opspilot_analyze: 解析 Excel 文件，返回 report.json 结构化数据
- opspilot_generate: 基于 report 数据生成 Word 实施文档
- opspilot_run: 完整流程 - 解析 + 生成

启动方式:
    python -m src.mcp.server
"""

import json
import sys
from pathlib import Path
from typing import Optional

# 确保项目根目录在 Python 路径中
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastmcp import FastMCP

from src.parser.excel_parser import ExcelParser
from src.renderer.template_renderer import TemplateRenderer

# 创建 MCP 服务实例
mcp = FastMCP("OpsPilot")


@mcp.tool()
def opspilot_analyze(
    excel_path: str, 
    config_path: str = "config/rules.yaml"
) -> dict:
    """
    解析 Excel 文件，生成结构化分析数据
    
    Args:
        excel_path: Excel 文件路径（绝对路径或相对于项目根目录）
        config_path: 规则配置文件路径，默认 config/rules.yaml
    
    Returns:
        report.json 结构化数据（符合 docs/report_schema.md v2.0 规范）
        
    Raises:
        FileNotFoundError: Excel 文件或配置文件不存在
        ValueError: 解析过程中出现错误
    """
    # 解析路径
    excel_file = Path(excel_path)
    if not excel_file.is_absolute():
        excel_file = project_root / excel_path
    
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = project_root / config_path
    
    # 验证文件存在
    if not excel_file.exists():
        raise FileNotFoundError(f"Excel 文件不存在: {excel_file}")
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")
    
    # 执行解析
    try:
        parser = ExcelParser(str(config_file))
        report = parser.parse(str(excel_file))
        return report
    except Exception as e:
        raise ValueError(f"Excel 解析失败: {str(e)}")


@mcp.tool()
def opspilot_generate(
    report: dict,
    template_path: str = "templates/template.docx",
    output_path: str = "output/实施文档.docx",
    config_path: str = "config/rules.yaml"
) -> str:
    """
    基于分析数据生成 Word 实施文档
    
    Args:
        report: report.json 结构化数据
        template_path: Word 模板文件路径
        output_path: 输出文件路径
        config_path: 规则配置文件路径
    
    Returns:
        生成的 Word 文件绝对路径
        
    Raises:
        ValueError: 渲染过程中出现错误
    """
    # 解析路径
    template_file = Path(template_path)
    if not template_file.is_absolute():
        template_file = project_root / template_path
    
    output_file = Path(output_path)
    if not output_file.is_absolute():
        output_file = project_root / output_path
    
    config_file = Path(config_path)
    if not config_file.is_absolute():
        config_file = project_root / config_path
    
    # 验证配置文件存在
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")
    
    # 执行渲染
    try:
        renderer = TemplateRenderer(str(config_file))
        result_path = renderer.render(report, str(template_file), str(output_file))
        return str(Path(result_path).resolve())
    except Exception as e:
        raise ValueError(f"Word 生成失败: {str(e)}")


@mcp.tool()
def opspilot_run(
    excel_path: str,
    config_path: str = "config/rules.yaml",
    template_path: str = "templates/template.docx",
    output_path: str = "output/实施文档.docx",
    force: bool = False
) -> str:
    """
    完整流程：解析 Excel 并生成 Word 文档
    
    Args:
        excel_path: Excel 文件路径
        config_path: 规则配置文件路径
        template_path: Word 模板文件路径
        output_path: 输出文件路径
        force: 是否跳过高危操作确认（当前未实现确认流程）
    
    Returns:
        生成的 Word 文件绝对路径
        
    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 处理过程中出现错误
    """
    # 1. 解析 Excel
    report = opspilot_analyze(excel_path, config_path)
    
    # 2. 检查高危操作（如果 force=False 且存在高危操作）
    if not force and report.get('has_risk_alerts', False):
        risk_count = report.get('summary', {}).get('high_risk_count', 0)
        # 注：MCP 协议下无法实现交互式确认，这里仅记录日志
        # 实际应用中应该返回错误或通过其他机制确认
        print(f"[警告] 检测到 {risk_count} 个高危操作，建议人工确认后使用 force=True 继续执行")
    
    # 3. 生成 Word
    result_path = opspilot_generate(report, template_path, output_path, config_path)
    
    return result_path


if __name__ == "__main__":
    # 启动 MCP 服务器
    mcp.run()
