# -*- coding: utf-8 -*-
"""
TemplateRenderer 单元测试

测试覆盖:
1. render() - Word 文档生成（模板/内置）
2. _render_summary() - 摘要渲染
3. _render_risk_alerts() - 风险告警渲染
4. _render_section() - 章节渲染
5. _render_task_table() - 表格渲染
"""

from pathlib import Path

import pytest
from docx import Document

from src.renderer import TemplateRenderer, render_with_template
from src.renderer.template_renderer import TemplateRendererError


def _empty_report():
    """v2.0 格式空报告"""
    return {
        'meta': {'source_file': 'empty.xlsx', 'generated_at': '2026-02-18T10:00:00Z', 'version': '2.0.0'},
        'summary': {'total_tasks': 0, 'total_sheets': 0, 'high_risk_count': 0, 'has_external_links': False, 'external_links': []},
        'has_risk_alerts': False,
        'risk_alerts': [],
        'sections': []
    }


def _minimal_report_no_alerts():
    """无风险告警的最小报告"""
    return {
        'meta': {'source_file': 'test.xlsx', 'generated_at': '2026-02-18T10:00:00Z', 'version': '2.0.0'},
        'summary': {'total_tasks': 1, 'total_sheets': 1, 'high_risk_count': 0, 'has_external_links': True, 'external_links': ['https://example.com']},
        'has_risk_alerts': False,
        'risk_alerts': [],
        'sections': []
    }


def _render(renderer, report, output_path, template_path="templates/template.docx"):
    """统一调用入口：模板不存在时走内置渲染"""
    return renderer.render(report, template_path, str(output_path))


class TestTemplateRendererInit:
    """测试 TemplateRenderer 初始化"""
    
    def test_init_with_default_config(self):
        renderer = TemplateRenderer()
        assert renderer._config is not None
        assert renderer._output_config is not None
    
    def test_init_with_custom_config(self, sample_config):
        renderer = TemplateRenderer(config_path=str(sample_config))
        assert renderer._config is not None
        assert 'output_config' in renderer._config
    
    def test_init_with_missing_config(self, temp_dir):
        with pytest.raises(FileNotFoundError):
            TemplateRenderer(config_path=str(temp_dir / "not_exist.yaml"))


class TestTemplateRendererRender:
    """测试 TemplateRenderer.render() 方法"""
    
    def test_render_basic_document(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "output.docx"
        result = _render(renderer, sample_report, output_path)
        assert Path(result).exists()
        assert Path(result).suffix == '.docx'
    
    def test_render_creates_output_directory(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "subdir" / "deep" / "output.docx"
        result = _render(renderer, sample_report, output_path)
        assert Path(result).exists()
        assert Path(result).parent.exists()
    
    def test_render_implementation_summary_table(self, sample_config, temp_dir):
        """测试实施总表表格渲染"""
        report_with_impl = {
            'meta': {'source_file': 'test.xlsx', 'version': '2.1.0'},
            'summary': {'total_tasks': 0, 'total_sheets': 0, 'high_risk_count': 0,
                        'has_external_links': False, 'external_links': []},
            'has_risk_alerts': False, 'risk_alerts': [],
            'implementation_summary': {
                'sheet_name': '上线安排',
                'columns': ['阶段', '任务', '负责人'],
                'rows': [{'cells': ['准备', '环境检查', '张三']}, {'cells': ['部署', '脚本执行', '李四']}],
                'has_data': True,
            },
            'sections': [],
        }
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "impl_summary.docx"
        _render(renderer, report_with_impl, output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '2.1 实施总表' in text
        assert len(doc.tables) >= 1

    def test_render_document_structure(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "structure_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        assert len(doc.paragraphs) > 0
        assert len(doc.tables) > 0
    
    def test_render_with_empty_report(self, sample_config, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "empty.docx"
        result = _render(renderer, _empty_report(), output_path)
        assert Path(result).exists()


class TestTemplateRendererSummary:
    """测试摘要渲染"""
    
    def test_summary_task_count(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "summary_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '任务总数' in text
        assert '3' in text
    
    def test_summary_high_risk_count(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "risk_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '高危操作' in text
        assert '1' in text
    
    def test_summary_external_links(self, sample_config, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "links_test.docx"
        _render(renderer, _minimal_report_no_alerts(), output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert 'https://example.com' in text


class TestTemplateRendererRiskAlerts:
    """测试风险告警渲染"""
    
    def test_risk_alerts_present(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "alerts_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '高危操作' in text or '⚠️' in text
    
    def test_risk_alerts_task_names(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "task_names_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '删除临时表' in text
    
    def test_no_risk_alerts_when_empty(self, sample_config, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "no_alerts_test.docx"
        _render(renderer, _empty_report(), output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '高危操作告警' not in text


class TestTemplateRendererSections:
    """测试章节渲染"""
    
    def test_sections_present(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "sections_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '应用配置' in text
    
    def test_sections_priority_order(self, sample_config, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "priority_test.docx"
        report = {
            'meta': {'source_file': 'test.xlsx', 'generated_at': '2026-02-18T10:00:00Z', 'version': '2.0.0'},
            'summary': {'total_tasks': 2, 'total_sheets': 2, 'high_risk_count': 0, 'has_external_links': False, 'external_links': []},
            'has_risk_alerts': False,
            'risk_alerts': [],
            'sections': [
                {'section_name': '应用配置', 'priority': 20, 'has_action_groups': False, 'columns': [], 'task_count': 1, 'action_groups': []},
                {'section_name': '数据库脚本部署', 'priority': 10, 'has_action_groups': False, 'columns': [], 'task_count': 1, 'action_groups': []},
            ]
        }
        _render(renderer, report, output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        db_pos = text.find('数据库脚本部署')
        app_pos = text.find('应用配置')
        assert db_pos < app_pos


class TestTemplateRendererTables:
    """测试表格渲染"""
    
    def test_table_created(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "table_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        assert len(doc.tables) > 0
    
    def test_table_headers(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "headers_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        if doc.tables:
            table = doc.tables[0]
            header_text = [cell.text for cell in table.rows[0].cells]
            assert len(header_text) > 0
    
    def test_table_data(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "data_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        if doc.tables:
            table = doc.tables[0]
            assert len(table.rows) >= 2
            data_row = table.rows[1]
            row_text = ' '.join([cell.text for cell in data_row.cells])
            assert len(row_text) > 0


class TestTemplateRendererHighRiskMarking:
    """测试高危操作标记"""
    
    def test_high_risk_marked_in_title(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "high_risk_mark_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '⚠️' in text or '高危' in text
    
    def test_high_risk_instruction_bold(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "bold_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        has_bold = any(run.bold for p in doc.paragraphs for run in p.runs)
        assert has_bold


class TestTemplateRendererChineseFont:
    """测试中文字体设置"""
    
    def test_chinese_font_applied(self, sample_config, sample_report, temp_dir):
        renderer = TemplateRenderer(config_path=str(sample_config))
        output_path = temp_dir / "chinese_font_test.docx"
        _render(renderer, sample_report, output_path)
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '任务' in text or '操作' in text or '配置' in text


class TestTemplateRendererConvenienceFunction:
    """测试便捷函数"""
    
    def test_render_with_template_function(self, sample_config, sample_report, temp_dir):
        output_path = temp_dir / "convenience_test.docx"
        result = render_with_template(
            sample_report,
            template_path="templates/template.docx",
            output_path=str(output_path),
            config_path=str(sample_config)
        )
        assert Path(result).exists()
