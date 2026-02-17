# -*- coding: utf-8 -*-
"""
ExcelParser 单元测试

测试覆盖:
1. parse() - 多 Sheet 解析
2. _build_field_mapping() - 动态表头匹配
3. _is_high_risk() - 高危操作检测
4. _sanitize_string() - 非法字符清理
5. 异常处理 - 空文件、缺失字段等
"""

import pytest
import pandas as pd

from src.parser import ExcelParser
from src.parser.excel_parser import (
    RequiredFieldMissingError,
    SheetNotFoundError,
    ExcelParserError
)


class TestExcelParserInit:
    """测试 ExcelParser 初始化"""
    
    def test_init_with_default_config(self):
        """测试使用默认配置初始化"""
        parser = ExcelParser()
        assert parser._config is not None
        assert parser._core_fields is not None
        assert parser._priority_rules is not None
    
    def test_init_with_custom_config(self, sample_config):
        """测试使用自定义配置初始化"""
        parser = ExcelParser(config_path=str(sample_config))
        assert parser._config is not None
        assert 'priority_rules' in parser._config
    
    def test_init_with_missing_config(self, temp_dir):
        """测试配置文件不存在时抛出异常"""
        with pytest.raises(FileNotFoundError):
            ExcelParser(config_path=str(temp_dir / "not_exist.yaml"))


class TestExcelParserParse:
    """测试 ExcelParser.parse() 方法"""
    
    def test_parse_basic_excel(self, sample_config, sample_excel):
        """测试解析基础 Excel 文件"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(sample_excel))
        
        # 验证基本结构
        assert 'meta' in result
        assert 'summary' in result
        assert 'sections' in result
        
        # 验证 meta
        assert result['meta']['source_file'] == 'test_checklist.xlsx'
        assert result['meta']['version'] == '1.0.0'
    
    def test_parse_multiple_sheets(self, sample_config, sample_excel):
        """测试解析多 Sheet Excel"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(sample_excel))
        
        # 验证解析了多个 Sheet
        assert result['summary']['total_sheets'] == 2
        
        # 验证 Section 名称
        section_names = [s['section_name'] for s in result['sections']]
        assert '数据库脚本部署' in section_names
        assert '上线代码包' in section_names
    
    def test_parse_task_count(self, sample_config, sample_excel):
        """测试任务计数正确"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(sample_excel))
        
        # Sheet1: 3个任务, Sheet2: 2个任务
        assert result['summary']['total_tasks'] == 5
    
    def test_parse_priority_order(self, sample_config, sample_excel):
        """测试章节按优先级排序"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(sample_excel))
        
        sections = result['sections']
        # 验证按 priority 排序
        priorities = [s['priority'] for s in sections]
        assert priorities == sorted(priorities)
    
    def test_parse_file_not_found(self, sample_config, temp_dir):
        """测试解析不存在的文件"""
        parser = ExcelParser(config_path=str(sample_config))
        with pytest.raises(FileNotFoundError):
            parser.parse(str(temp_dir / "not_exist.xlsx"))
    
    def test_parse_empty_excel(self, sample_config, empty_excel):
        """测试解析空 Excel 文件"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(empty_excel))
        
        # 空 Excel 应该返回空 sections
        assert result['summary']['total_tasks'] == 0
        assert result['summary']['total_sheets'] == 0


class TestExcelParserHighRisk:
    """测试高危操作检测"""
    
    def test_detect_delete_as_high_risk(self, sample_config, sample_excel_with_high_risk):
        """测试检测删除操作为高危"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(sample_excel_with_high_risk))
        
        assert result['summary']['high_risk_count'] >= 1
        
        # 验证风险告警
        assert len(result['risk_alerts']) >= 1
        alert_actions = [a['action_type'] for a in result['risk_alerts']]
        assert '删除' in alert_actions
    
    def test_detect_offline_as_high_risk(self, sample_config, sample_excel_with_high_risk):
        """测试检测下线操作为高危"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(sample_excel_with_high_risk))
        
        # 删除和下线都是高危
        assert result['summary']['high_risk_count'] >= 2
    
    def test_high_risk_in_action_library(self, sample_config):
        """测试 action_library 中的高危标记"""
        parser = ExcelParser(config_path=str(sample_config))
        
        # 删除在 action_library 中标记为高危
        assert parser._is_high_risk('删除') is True
        assert parser._is_high_risk('下线') is True
        assert parser._is_high_risk('新增') is False
        assert parser._is_high_risk('修改') is False
    
    def test_high_risk_keyword_detection(self, sample_config):
        """测试高危关键字检测"""
        parser = ExcelParser(config_path=str(sample_config))
        
        # 包含高危关键字的操作
        assert parser._is_high_risk('批量删除') is True  # 包含"删除"
        assert parser._is_high_risk('服务下线') is True  # 包含"下线"
        assert parser._is_high_risk('重建索引') is True  # 包含"重建"


class TestExcelParserFieldMapping:
    """测试动态表头解析"""
    
    def test_exact_match(self, sample_config):
        """测试精确匹配表头"""
        parser = ExcelParser(config_path=str(sample_config))
        
        columns = ['任务名', '操作类型', '执行人']
        mapping = parser._build_field_mapping(columns)
        
        assert mapping['task_name'] == '任务名'
        assert mapping['action_type'] == '操作类型'
        assert mapping['executor'] == '执行人'
    
    def test_alias_match(self, sample_config):
        """测试别名匹配表头"""
        parser = ExcelParser(config_path=str(sample_config))
        
        # 使用别名
        columns = ['任务名称', '操作', '负责人']
        mapping = parser._build_field_mapping(columns)
        
        assert mapping['task_name'] == '任务名称'
        assert mapping['action_type'] == '操作'
        assert mapping['executor'] == '负责人'
    
    def test_case_insensitive_match(self, sample_config):
        """测试大小写不敏感匹配"""
        parser = ExcelParser(config_path=str(sample_config))
        
        columns = ['TASK NAME', 'Action', '执行人']
        mapping = parser._build_field_mapping(columns)
        
        # 应该能匹配（忽略大小写）
        assert mapping['task_name'] is not None or mapping['action_type'] is not None
    
    def test_partial_match(self, sample_config):
        """测试部分匹配"""
        parser = ExcelParser(config_path=str(sample_config))
        
        # 包含匹配
        columns = ['任务名称(中文)', '操作类型说明', '执行人员']
        mapping = parser._build_field_mapping(columns)
        
        # 应该能部分匹配到
        assert mapping['task_name'] == '任务名称(中文)'
        assert mapping['action_type'] == '操作类型说明'
    
    def test_missing_field(self, sample_config):
        """测试缺失字段"""
        parser = ExcelParser(config_path=str(sample_config))
        
        columns = ['任务名']  # 缺少操作类型
        mapping = parser._build_field_mapping(columns)
        
        assert mapping['task_name'] == '任务名'
        assert mapping['action_type'] is None


class TestExcelParserValidation:
    """测试字段验证"""
    
    def test_validate_required_fields_pass(self, sample_config):
        """测试必填字段验证通过"""
        parser = ExcelParser(config_path=str(sample_config))
        
        mapping = {
            'task_name': '任务名',
            'action_type': '操作类型',
            'deploy_unit': None,
            'executor': None
        }
        
        # 不应抛出异常
        parser._validate_required_fields(mapping)
    
    def test_validate_required_fields_fail(self, sample_config):
        """测试必填字段验证失败"""
        parser = ExcelParser(config_path=str(sample_config))
        
        mapping = {
            'task_name': '任务名',
            'action_type': None,  # 必填但缺失
            'deploy_unit': None,
            'executor': None
        }
        
        with pytest.raises(RequiredFieldMissingError) as exc_info:
            parser._validate_required_fields(mapping)
        
        assert 'action_type' in str(exc_info.value)
    
    def test_parse_malformed_excel(self, sample_config, malformed_excel):
        """测试解析格式错误的 Excel"""
        parser = ExcelParser(config_path=str(sample_config))
        
        with pytest.raises(RequiredFieldMissingError):
            parser.parse(str(malformed_excel))


class TestExcelParserSanitize:
    """测试字符串清理"""
    
    def test_sanitize_control_chars(self, sample_config):
        """测试清理控制字符"""
        parser = ExcelParser(config_path=str(sample_config))
        
        # 包含控制字符的字符串
        dirty = "任务\x00名称\x0b测试"
        clean = parser._sanitize_string(dirty)
        
        assert '\x00' not in clean
        assert '\x0b' not in clean
        assert '任务' in clean
    
    def test_sanitize_whitespace(self, sample_config):
        """测试清理多余空白"""
        parser = ExcelParser(config_path=str(sample_config))
        
        dirty = "任务   名称\t\t测试"
        clean = parser._sanitize_string(dirty)
        
        # 连续空白应替换为单个空格
        assert '  ' not in clean
        assert '\t' not in clean
    
    def test_sanitize_empty_string(self, sample_config):
        """测试空字符串"""
        parser = ExcelParser(config_path=str(sample_config))
        
        assert parser._sanitize_string('') == ''
        assert parser._sanitize_string('   ') == ''


class TestExcelParserActionGroups:
    """测试操作组聚合"""
    
    def test_action_group_aggregation(self, sample_config, sample_excel):
        """测试相同操作类型聚合"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(sample_excel))
        
        # 找到数据库脚本部署章节
        db_section = next(
            (s for s in result['sections'] if s['section_name'] == '数据库脚本部署'),
            None
        )
        
        assert db_section is not None
        
        # 验证 action_groups
        action_types = [g['action_type'] for g in db_section['action_groups']]
        assert '新增' in action_types
        assert '删除' in action_types
    
    def test_action_group_instruction(self, sample_config, sample_excel):
        """测试操作说明从 action_library 获取"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(sample_excel))
        
        for section in result['sections']:
            for group in section['action_groups']:
                assert 'instruction' in group
                assert group['instruction']  # 非空
    
    def test_action_group_tasks(self, sample_config, sample_excel):
        """测试任务数据完整性"""
        parser = ExcelParser(config_path=str(sample_config))
        result = parser.parse(str(sample_excel))
        
        for section in result['sections']:
            for group in section['action_groups']:
                for task in group['tasks']:
                    assert 'task_name' in task
                    assert 'raw_data' in task


class TestExcelParserGetSheets:
    """测试 get_sheets() 方法"""
    
    def test_get_sheets_returns_priority_order(self, sample_config):
        """测试返回按优先级排序的 Sheet 列表"""
        parser = ExcelParser(config_path=str(sample_config))
        sheets = parser.get_sheets()
        
        # 验证返回的 sheets
        assert '数据库脚本部署' in sheets
        assert '上线代码包' in sheets
        assert '应用配置' in sheets
        
        # 验证顺序：数据库脚本部署(10) < 上线代码包(15) < 应用配置(20)
        assert sheets.index('数据库脚本部署') < sheets.index('上线代码包')
        assert sheets.index('上线代码包') < sheets.index('应用配置')


class TestExcelParserGetColumns:
    """测试 get_columns_for_sheet() 方法"""
    
    def test_get_columns_for_known_sheet(self, sample_config):
        """测试获取已知 Sheet 的列配置"""
        parser = ExcelParser(config_path=str(sample_config))
        
        columns = parser.get_columns_for_sheet('数据库脚本部署')
        assert '脚本名称' in columns
        assert '执行顺序' in columns
    
    def test_get_columns_for_unknown_sheet(self, sample_config):
        """测试获取未知 Sheet 使用默认列"""
        parser = ExcelParser(config_path=str(sample_config))
        
        columns = parser.get_columns_for_sheet('未知Sheet')
        assert '任务名' in columns  # 默认列
