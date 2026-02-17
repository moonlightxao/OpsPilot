#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpsPilot - 运维副驾驶
自动化部署方案生成工具

Usage:
    python main.py analyze <excel_file>      # 分析阶段：输出 report.json
    python main.py generate <report_file>    # 生成阶段：输出 Word 文档
    python main.py run <excel_file>          # 完整流程：分析 + 生成
"""

import json
import sys
import click
from pathlib import Path

from src.parser import ExcelParser


def safe_echo(message: str, err: bool = False) -> None:
    """
    安全输出函数，兼容 Windows GBK 控制台

    自动检测终端编码，不支持 UTF-8 时将 emoji 和特殊符号替换为 ASCII 文本
    """
    # 检测终端是否支持 UTF-8
    try:
        # 尝试编码测试
        if sys.stdout.encoding and sys.stdout.encoding.lower().replace('-', '') != 'utf8':
            # 非 UTF-8 编码（如 GBK），替换 emoji 和特殊符号为文本
            replacements = {
                '⚠️': '[!]',
                '✅': '[OK]',
                '❌': '[X]',
                '•': '-',
                '→': '->',
                '←': '<-',
            }
            for old, new in replacements.items():
                message = message.replace(old, new)
    except (AttributeError, TypeError):
        pass

    click.echo(message, err=err)


@click.group()
def cli():
    """OpsPilot - 运维副驾驶"""
    pass


@cli.command()
@click.argument('excel_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='output/report.json', help='输出文件路径')
@click.option('--config', '-c', default='config/rules.yaml', help='规则配置文件路径')
def analyze(excel_file: str, output: str, config: str):
    """
    分析阶段：解析 Excel，生成中间态 report.json

    此阶段会输出分析摘要，包括任务统计、风险提示、链接列表。
    高危操作会被标记，需要人工确认后方可进入生成阶段。
    """
    click.echo(f"[Analyze] 正在解析: {excel_file}")

    try:
        # 调用 Parser 模块
        parser = ExcelParser(config_path=config)
        report = parser.parse(excel_file)

        # 确保输出目录存在
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存 report.json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 输出分析摘要
        summary = report.get('summary', {})
        click.echo(f"[Analyze] 任务总数: {summary.get('total_tasks', 0)}")
        click.echo(f"[Analyze] 解析 Sheet 数: {summary.get('total_sheets', 0)}")
        click.echo(f"[Analyze] 高危操作数: {summary.get('high_risk_count', 0)}")

        # 风险提示
        risk_alerts = report.get('risk_alerts', [])
        if risk_alerts:
            safe_echo("\n[Analyze] ⚠️ 高危操作告警:")
            for alert in risk_alerts:
                safe_echo(f"  - [{alert['sheet_name']}] {alert['action_type']}: {alert['task_count']} 个任务")
                for task_name in alert['task_names'][:3]:  # 最多显示3个
                    safe_echo(f"      • {task_name}")
                if len(alert['task_names']) > 3:
                    safe_echo(f"      ... 等共 {len(alert['task_names'])} 个任务")

        safe_echo(f"\n[Analyze] 输出报告: {output}")

        if summary.get('high_risk_count', 0) > 0:
            safe_echo("[Analyze] ⚠️ 检测到高危操作，请确认风险提示后执行 generate 命令")
        else:
            safe_echo("[Analyze] 分析完成，可执行 generate 命令生成文档")

    except Exception as e:
        click.echo(f"[Analyze] 错误: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('report_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='output/实施文档.docx', help='输出文件路径')
@click.option('--template', '-t', default='templates/实施文档.doc', help='模板文件路径')
@click.option('--config', '-c', default='config/rules.yaml', help='规则配置文件路径')
def generate(report_file: str, output: str, template: str, config: str):
    """
    生成阶段：读取 report.json，渲染 Word 实施文档

    注意：此阶段应在人工确认分析结果后执行。
    """
    click.echo(f"[Generate] 正在读取: {report_file}")

    try:
        # 读取 report.json
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)

        # 调用 Renderer 模块
        from src.renderer import WordRenderer
        renderer = WordRenderer(config_path=config)

        # 执行渲染
        output_path = renderer.render(report, output)
        click.echo(f"[Generate] 输出文档: {output_path}")
        click.echo("[Generate] 文档生成完成")

    except ImportError:
        click.echo("[Generate] 错误: Renderer 模块尚未实现", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"[Generate] 错误: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument('excel_file', type=click.Path(exists=True))
@click.option('--output', '-o', default='output/实施文档.docx', help='输出文件路径')
@click.option('--config', '-c', default='config/rules.yaml', help='规则配置文件路径')
@click.option('--force', '-f', is_flag=True, help='跳过高危操作确认')
def run(excel_file: str, output: str, config: str, force: bool):
    """
    完整流程：分析 + 生成

    警告：此命令会跳过人工确认环节，仅建议在无高危操作时使用。
    使用 --force 参数可强制执行包含高危操作的流程。
    """
    click.echo(f"[Run] 完整流程启动: {excel_file}")

    try:
        # 阶段 1: 分析
        click.echo("[Run] 阶段 1/2: 分析中...")
        parser = ExcelParser(config_path=config)
        report = parser.parse(excel_file)

        # 检查高危操作
        high_risk_count = report.get('summary', {}).get('high_risk_count', 0)
        if high_risk_count > 0 and not force:
            safe_echo(f"[Run] ⚠️ 检测到 {high_risk_count} 个高危操作，请使用 --force 参数强制执行")
            raise click.Abort()

        # 保存中间报告
        report_path = Path(output).with_suffix('.json')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 阶段 2: 生成
        click.echo("[Run] 阶段 2/2: 生成中...")
        from src.renderer import WordRenderer
        renderer = WordRenderer(config_path=config)
        output_path = renderer.render(report, output)

        click.echo(f"[Run] 完成: {output_path}")

    except ImportError:
        click.echo("[Run] 错误: Renderer 模块尚未实现", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"[Run] 错误: {e}", err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()
