# -*- coding: utf-8 -*-
"""
WordRenderer 单元测试

测试覆盖:
1. render() - Word 文档生成
2. _render_summary() - 摘要渲染
3. _render_risk_alerts() - 风险告警渲染
4. _render_section() - 章节渲染
5. _render_task_table() - 表格渲染
"""

import json
from pathlib import Path

import pytest
from docx import Document

from src.renderer import WordRenderer
from src.renderer.word_renderer import WordRendererError


class TestWordRendererInit:
    """测试 WordRenderer 初始化"""
    
    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        renderer = WordRenderer()
        assert renderer._config is not None
        assert renderer._output_config is not None
    
    def test_init_with_custom_config(self, sample_config):
        """测试使用自定义配置初始化"""
        renderer = WordRenderer(config_path=str(sample_config))
        assert renderer._config is not None
        assert 'output_config' in renderer._config
    
    def test_init_with_missing_config(self, temp_dir):
        """测试配置文件不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            WordRenderer(config_path=str(temp_dir / "not_exist.yaml"))


class TestWordRendererRender:
    """测试 WordRenderer.render() 方法"""
    
    def test_render_basic_document(self, sample_config, sample_report, temp_dir):
        """测试生成基础 Word 文档"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "output.docx"
        
        result = renderer.render(sample_report, str(output_path))
        
        assert Path(result).exists()
        assert Path(result).suffix == '.docx'
    
    def test_render_creates_output_directory(self, sample_config, sample_report, temp_dir):
        """测试自动创建输出目录"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "subdir" / "deep" / "output.docx"
        
        result = renderer.render(sample_report, str(output_path))
        
        assert Path(result).exists()
        assert Path(result).parent.exists()
    
    def test_render_document_structure(self, sample_config, sample_report, temp_dir):
        """测试文档结构正确"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "structure_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        # 打开文档验证结构
        doc = Document(str(output_path))
        
        # 验证有内容
        assert len(doc.paragraphs) > 0
        assert len(doc.tables) > 0
    
    def test_render_with_empty_report(self, sample_config, temp_dir):
        """测试空报告"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "empty.docx"
        
        empty_report = {
            'meta': {'source_file': 'empty.xlsx', 'generated_at': '2026-02-18T10:00:00Z', 'version': '1.0.0'},
            'summary': {'total_tasks': 0, 'total_sheets': 0, 'high_risk_count': 0, 'external_links': []},
            'risk_alerts': [],
            'sections': []
        }
        
        result = renderer.render(empty_report, str(output_path))
        assert Path(result).exists()


class TestWordRendererSummary:
    """测试摘要渲染"""
    
    def test_summary_task_count(self, sample_config, sample_report, temp_dir):
        """测试摘要显示任务总数"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "summary_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        
        assert '任务总数' in text
        assert '3' in text  # sample_report 中 total_tasks = 3
    
    def test_summary_high_risk_count(self, sample_config, sample_report, temp_dir):
        """测试摘要显示高危操作数"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "risk_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        
        assert '高危操作' in text
        assert '1' in text  # sample_report 中 high_risk_count = 1
    
    def test_summary_external_links(self, sample_config, temp_dir):
        """测试摘要显示外部链接"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "links_test.docx"
        
        report = {
            'meta': {'source_file': 'test.xlsx', 'generated_at': '2026-02-18T10:00:00Z', 'version': '1.0.0'},
            'summary': {'total_tasks': 1, 'total_sheets': 1, 'high_risk_count': 0, 
                       'external_links': ['https://example.com']},
            'risk_alerts': [],
            'sections': []
        }
        
        renderer.render(report, str(output_path))
        
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        
        assert 'https://example.com' in text


class TestWordRendererRiskAlerts:
    """测试风险告警渲染"""
    
    def test_risk_alerts_present(self, sample_config, sample_report, temp_dir):
        """测试风险告警显示"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "alerts_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        
        # 验证有高危操作告警
        assert '高危操作' in text or '⚠️' in text
    
    def test_risk_alerts_task_names(self, sample_config, sample_report, temp_dir):
        """测试风险告警显示任务名"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "task_names_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        
        # 验证高危任务名显示
        assert '删除临时表' in text
    
    def test_no_risk_alerts_when_empty(self, sample_config, temp_dir):
        """测试无风险告警时不显示"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "no_alerts_test.docx"
        
        report = {
            'meta': {'source_file': 'test.xlsx', 'generated_at': '2026-02-18T10:00:00Z', 'version': '1.0.0'},
            'summary': {'total_tasks': 0, 'total_sheets': 0, 'high_risk_count': 0, 'external_links': []},
            'risk_alerts': [],  # 无风险告警
            'sections': []
        }
        
        renderer.render(report, str(output_path))
        
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        
        # 不应显示风险告警标题
        assert '高危操作告警' not in text


class TestWordRendererSections:
    """测试章节渲染"""
    
    def test_sections_present(self, sample_config, sample_report, temp_dir):
        """测试章节显示"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "sections_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        
        # 验证章节名显示
        assert '应用配置' in text
    
    def test_sections_priority_order(self, sample_config, temp_dir):
        """测试章节按优先级排序"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "priority_test.docx"
        
        report = {
            'meta': {'source_file': 'test.xlsx', 'generated_at': '2026-02-18T10:00:00Z', 'version': '1.0.0'},
            'summary': {'total_tasks': 2, 'total_sheets': 2, 'high_risk_count': 0, 'external_links': []},
            'risk_alerts': [],
            'sections': [
                {'section_name': '应用配置', 'priority': 20, 'task_count': 1, 'action_groups': []},
                {'section_name': '数据库脚本部署', 'priority': 10, 'task_count': 1, 'action_groups': []},
            ]
        }
        
        renderer.render(report, str(output_path))
        
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        
        # 验证顺序：数据库脚本部署(10) 在 应用配置(20) 之前
        db_pos = text.find('数据库脚本部署')
        app_pos = text.find('应用配置')
        assert db_pos < app_pos


class TestWordRendererTables:
    """测试表格渲染"""
    
    def test_table_created(self, sample_config, sample_report, temp_dir):
        """测试表格创建"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "table_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        
        # 应该有表格
        assert len(doc.tables) > 0
    
    def test_table_headers(self, sample_config, sample_report, temp_dir):
        """测试表格表头"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "headers_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        
        # 检查第一个表格的表头
        if doc.tables:
            table = doc.tables[0]
            header_row = table.rows[0]
            header_text = [cell.text for cell in header_row.cells]
            
            # 应该有表头内容
            assert len(header_text) > 0
    
    def test_table_data(self, sample_config, sample_report, temp_dir):
        """测试表格数据"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "data_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        
        # 检查表格包含数据
        if doc.tables:
            table = doc.tables[0]
            # 至少有表头 + 1 行数据
            assert len(table.rows) >= 2
            
            # 数据行应该包含任务名
            data_row = table.rows[1]
            row_text = ' '.join([cell.text for cell in data_row.cells])
            assert len(row_text) > 0


class TestWordRendererHighRiskMarking:
    """测试高危操作标记"""
    
    def test_high_risk_marked_in_title(self, sample_config, sample_report, temp_dir):
        """测试高危操作在标题中标记"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "high_risk_mark_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        text = '\n'.join([p.text for p in doc.paragraphs])
        
        # 高危操作应该有 ⚠️ 标记
        assert '⚠️' in text or '高危' in text
    
    def test_high_risk_instruction_bold(self, sample_config, sample_report, temp_dir):
        """测试高危操作说明加粗"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "bold_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        
        # 检查是否有加粗文本
        has_bold = False
        for paragraph in doc.paragraphs:
            for run in paragraph.runs:
                if run.bold:
                    has_bold = True
                    break
        
        assert has_bold


class TestWordRendererChineseFont:
    """测试中文字体设置"""
    
    def test_chinese_font_applied(self, sample_config, sample_report, temp_dir):
        """测试中文字体应用"""
        renderer = WordRenderer(config_path=str(sample_config))
        output_path = temp_dir / "chinese_font_test.docx"
        
        renderer.render(sample_report, str(output_path))
        
        doc = Document(str(output_path))
        
        # 文档应该能正常打开并包含中文
        text = '\n'.join([p.text for p in doc.paragraphs])
        assert '任务' in text or '操作' in text or '配置' in text


class TestWordRendererConvenienceFunction:
    """测试便捷函数"""
    
    def test_render_report_function(self, sample_config, sample_report, temp_dir):
        """测试 render_report 便捷函数"""
        from src.renderer import render_report
        
        output_path = temp_dir / "convenience_test.docx"
        result = render_report(sample_report, str(output_path), str(sample_config))
        
        assert Path(result).exists()
