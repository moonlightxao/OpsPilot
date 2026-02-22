# -*- coding: utf-8 -*-
"""
MCP Server 集成测试

测试覆盖:
1. opspilot_analyze - Excel 解析 MCP Tool
2. opspilot_generate - Word 生成 MCP Tool
3. opspilot_run - 完整流程 MCP Tool
4. 错误处理 - 文件不存在、无效参数等

注意：此测试模块需要 fastmcp 依赖
"""

import pytest

# 检查 fastmcp 是否可用 - 在模块级别跳过
fastmcp = pytest.importorskip("fastmcp", reason="fastmcp not installed")

from pathlib import Path

# 导入 MCP Server 模块（此时 fastmcp 已确认可用）
from src.mcp.server import (
    opspilot_analyze,
    opspilot_generate,
    opspilot_run,
    project_root
)


class TestMCPAnalyze:
    """测试 opspilot_analyze MCP Tool"""
    
    def test_analyze_basic_excel(self, sample_config, sample_excel):
        """测试解析基础 Excel 文件"""
        result = opspilot_analyze(
            str(sample_excel),
            config_path=str(sample_config)
        )
        
        # 验证返回结构
        assert 'meta' in result
        assert 'summary' in result
        assert 'sections' in result
        
        # 验证 v2.0 协议
        assert result['meta']['version'] == '2.0.0'
        
        # 验证任务数
        assert result['summary']['total_tasks'] == 5
    
    def test_analyze_with_absolute_path(self, sample_config, sample_excel):
        """测试使用绝对路径解析"""
        abs_path = str(sample_excel.resolve())
        result = opspilot_analyze(abs_path, config_path=str(sample_config))
        
        assert result['meta']['source_file'] == sample_excel.name
    
    def test_analyze_file_not_found(self, sample_config, temp_dir):
        """测试解析不存在的文件"""
        with pytest.raises(FileNotFoundError) as exc_info:
            opspilot_analyze(
                str(temp_dir / "not_exist.xlsx"),
                config_path=str(sample_config)
            )
        assert "Excel 文件不存在" in str(exc_info.value)
    
    def test_analyze_config_not_found(self, sample_excel, temp_dir):
        """测试配置文件不存在"""
        with pytest.raises(FileNotFoundError) as exc_info:
            opspilot_analyze(
                str(sample_excel),
                config_path=str(temp_dir / "not_exist.yaml")
            )
        assert "配置文件不存在" in str(exc_info.value)
    
    def test_analyze_high_risk_detection(self, sample_config, sample_excel_with_high_risk):
        """测试高危操作检测"""
        result = opspilot_analyze(
            str(sample_excel_with_high_risk),
            config_path=str(sample_config)
        )
        
        assert result['has_risk_alerts'] is True
        assert result['summary']['high_risk_count'] > 0
    
    def test_analyze_cells_format(self, sample_config, sample_excel):
        """测试 v2.0 协议 cells 格式"""
        result = opspilot_analyze(
            str(sample_excel),
            config_path=str(sample_config)
        )
        
        for section in result['sections']:
            for group in section.get('action_groups', []):
                for task in group.get('tasks', []):
                    assert 'cells' in task
                    assert isinstance(task['cells'], list)


class TestMCPGenerate:
    """测试 opspilot_generate MCP Tool"""
    
    def test_generate_basic_document(self, sample_config, sample_report, temp_dir):
        """测试生成基础 Word 文档"""
        output_path = temp_dir / "mcp_output.docx"
        
        result = opspilot_generate(
            sample_report,
            template_path="templates/template.docx",
            output_path=str(output_path),
            config_path=str(sample_config)
        )
        
        assert Path(result).exists()
        assert Path(result).suffix == '.docx'
    
    def test_generate_returns_absolute_path(self, sample_config, sample_report, temp_dir):
        """测试返回绝对路径"""
        output_path = temp_dir / "absolute_test.docx"
        
        result = opspilot_generate(
            sample_report,
            output_path=str(output_path),
            config_path=str(sample_config)
        )
        
        assert Path(result).is_absolute()
    
    def test_generate_creates_output_directory(self, sample_config, sample_report, temp_dir):
        """测试自动创建输出目录"""
        output_path = temp_dir / "deep" / "nested" / "dir" / "output.docx"
        
        result = opspilot_generate(
            sample_report,
            output_path=str(output_path),
            config_path=str(sample_config)
        )
        
        assert Path(result).exists()
        assert Path(result).parent.exists()


class TestMCPRun:
    """测试 opspilot_run MCP Tool"""
    
    def test_run_full_flow(self, sample_config, sample_excel, temp_dir):
        """测试完整流程"""
        output_path = temp_dir / "full_flow.docx"
        
        result = opspilot_run(
            str(sample_excel),
            config_path=str(sample_config),
            output_path=str(output_path)
        )
        
        assert Path(result).exists()
        assert Path(result).suffix == '.docx'
    
    def test_run_with_force(self, sample_config, sample_excel_with_high_risk, temp_dir):
        """测试强制执行高危操作"""
        output_path = temp_dir / "forced.docx"
        
        result = opspilot_run(
            str(sample_excel_with_high_risk),
            config_path=str(sample_config),
            output_path=str(output_path),
            force=True
        )
        
        assert Path(result).exists()
    
    def test_run_high_risk_warning(self, sample_config, sample_excel_with_high_risk, temp_dir, capsys):
        """测试高危操作警告输出"""
        output_path = temp_dir / "warning.docx"
        
        result = opspilot_run(
            str(sample_excel_with_high_risk),
            config_path=str(sample_config),
            output_path=str(output_path),
            force=False  # 不强制执行
        )
        
        # 应该仍然生成文件（MCP 协议下无法交互确认）
        assert Path(result).exists()
        
        # 检查警告输出
        captured = capsys.readouterr()
        assert "高危操作" in captured.out or "警告" in captured.out
    
    def test_run_file_not_found(self, sample_config, temp_dir):
        """测试文件不存在错误"""
        output_path = temp_dir / "not_found.docx"
        
        with pytest.raises(FileNotFoundError):
            opspilot_run(
                str(temp_dir / "not_exist.xlsx"),
                config_path=str(sample_config),
                output_path=str(output_path)
            )


class TestMCPProtocolCompliance:
    """测试 MCP 协议合规性"""
    
    def test_analyze_returns_dict(self, sample_config, sample_excel):
        """测试 analyze 返回字典类型"""
        result = opspilot_analyze(
            str(sample_excel),
            config_path=str(sample_config)
        )
        
        assert isinstance(result, dict)
    
    def test_generate_returns_string(self, sample_config, sample_report, temp_dir):
        """测试 generate 返回字符串路径"""
        output_path = temp_dir / "string_test.docx"
        
        result = opspilot_generate(
            sample_report,
            output_path=str(output_path),
            config_path=str(sample_config)
        )
        
        assert isinstance(result, str)
    
    def test_run_returns_string(self, sample_config, sample_excel, temp_dir):
        """测试 run 返回字符串路径"""
        output_path = temp_dir / "string_run.docx"
        
        result = opspilot_run(
            str(sample_excel),
            config_path=str(sample_config),
            output_path=str(output_path)
        )
        
        assert isinstance(result, str)
    
    def test_report_schema_v2_compliance(self, sample_config, sample_excel):
        """测试 report 符合 v2.0 schema"""
        result = opspilot_analyze(
            str(sample_excel),
            config_path=str(sample_config)
        )
        
        # 必填字段检查
        assert 'meta' in result
        assert 'version' in result['meta']
        assert 'summary' in result
        assert 'sections' in result
        assert 'has_risk_alerts' in result
        
        # summary 字段检查
        assert 'total_tasks' in result['summary']
        assert 'total_sheets' in result['summary']
        assert 'high_risk_count' in result['summary']
        assert 'has_external_links' in result['summary']
        
        # sections 字段检查
        for section in result['sections']:
            assert 'section_name' in section
            assert 'priority' in section
            assert 'has_action_groups' in section
            assert 'columns' in section
            assert 'action_groups' in section
            
            for group in section.get('action_groups', []):
                assert 'action_type' in group
                assert 'instruction' in group
                assert 'is_high_risk' in group
                assert 'task_count' in group
                assert 'tasks' in group
                
                for task in group.get('tasks', []):
                    assert 'cells' in task
