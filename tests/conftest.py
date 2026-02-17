# -*- coding: utf-8 -*-
"""
测试配置与共享 fixtures
"""
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir):
    """创建测试用 rules.yaml 配置文件"""
    config_data = {
        'priority_rules': {
            "数据库脚本部署": 10,
            "上线代码包": 15,
            "应用配置": 20,
        },
        'action_library': {
            "新增": {
                'instruction': "新增以下配置：",
                'is_high_risk': False,
                'render_table': True
            },
            "修改": {
                'instruction': "修改以下配置：",
                'is_high_risk': False,
                'render_table': True
            },
            "删除": {
                'instruction': "【高危操作】删除以下配置：",
                'is_high_risk': True,
                'render_table': True
            },
            "下线": {
                'instruction': "【高危操作】下线以下配置：",
                'is_high_risk': True,
                'render_table': True
            },
        },
        'high_risk_keywords': ["删除", "下线", "重建"],
        'sheet_column_mapping': {
            "数据库脚本部署": {
                'columns': ["脚本名称", "执行顺序", "数据库", "执行人", "备注"]
            },
            "上线代码包": {
                'columns': ["应用名称", "版本号", "部署环境", "执行人", "备注"]
            },
        },
        'default_columns': ["任务名", "操作类型", "部署单元", "执行人", "备注"],
        'core_fields': {
            'task_name': {
                'aliases': ["任务名", "任务名称", "Task Name"],
                'required': True
            },
            'action_type': {
                'aliases': ["操作类型", "操作", "Action"],
                'required': True
            },
            'deploy_unit': {
                'aliases': ["部署单元", "应用名", "服务名"],
                'required': False
            },
            'executor': {
                'aliases': ["执行人", "负责人"],
                'required': False
            },
            'external_link': {
                'aliases': ["外部链接", "链接", "URL"],
                'required': False
            },
        },
        'output_config': {
            'title_style': {
                'font_name': "微软雅黑",
                'font_size': 16,
                'bold': True
            },
            'body_style': {
                'font_name': "宋体",
                'font_size': 11
            },
            'table_header_style': {
                'font_name': "微软雅黑",
                'font_size': 10,
                'bold': True,
                'background_color': "#D9E2F3"
            }
        }
    }
    
    config_path = temp_dir / "rules.yaml"
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
    
    return config_path


@pytest.fixture
def sample_excel(temp_dir):
    """创建测试用 Excel 文件"""
    # Sheet 1: 数据库脚本部署
    df1 = pd.DataFrame({
        '任务名': ['创建用户表', '添加索引', '删除临时表'],
        '操作类型': ['新增', '新增', '删除'],
        '执行人': ['张三', '李四', '王五'],
        '备注': ['初始化脚本', '性能优化', '清理废弃数据']
    })
    
    # Sheet 2: 上线代码包
    df2 = pd.DataFrame({
        '任务名称': ['部署服务A', '升级服务B'],
        '操作': ['部署', '升级'],
        '执行人': ['张三', '李四'],
        '备注': ['v1.0.0', 'v2.0.0']
    })
    
    excel_path = temp_dir / "test_checklist.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df1.to_excel(writer, sheet_name='数据库脚本部署', index=False)
        df2.to_excel(writer, sheet_name='上线代码包', index=False)
    
    return excel_path


@pytest.fixture
def sample_excel_with_high_risk(temp_dir):
    """创建包含高危操作的测试 Excel 文件"""
    df = pd.DataFrame({
        '任务名': ['删除用户数据', '下线服务C', '普通修改'],
        '操作类型': ['删除', '下线', '修改'],
        '执行人': ['张三', '李四', '王五'],
        '备注': ['高危操作', '高危操作', '普通操作']
    })
    
    excel_path = temp_dir / "test_high_risk.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='应用配置', index=False)
    
    return excel_path


@pytest.fixture
def empty_excel(temp_dir):
    """创建空的测试 Excel 文件"""
    df = pd.DataFrame()
    excel_path = temp_dir / "test_empty.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='空Sheet', index=False)
    return excel_path


@pytest.fixture
def malformed_excel(temp_dir):
    """创建缺少必填字段的测试 Excel 文件"""
    df = pd.DataFrame({
        '任务描述': ['任务1', '任务2'],  # 缺少 '任务名' 和 '操作类型'
        '执行人': ['张三', '李四']
    })
    
    excel_path = temp_dir / "test_malformed.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='应用配置', index=False)
    
    return excel_path


@pytest.fixture
def sample_report():
    """创建测试用 report.json 数据"""
    return {
        'meta': {
            'source_file': 'test_checklist.xlsx',
            'generated_at': '2026-02-18T10:00:00Z',
            'version': '1.0.0'
        },
        'summary': {
            'total_tasks': 3,
            'total_sheets': 1,
            'high_risk_count': 1,
            'external_links': []
        },
        'risk_alerts': [
            {
                'sheet_name': '应用配置',
                'action_type': '删除',
                'task_count': 1,
                'task_names': ['删除临时表']
            }
        ],
        'sections': [
            {
                'section_name': '应用配置',
                'priority': 20,
                'task_count': 3,
                'action_groups': [
                    {
                        'action_type': '新增',
                        'instruction': '新增以下配置：',
                        'is_high_risk': False,
                        'tasks': [
                            {
                                'task_name': '创建用户表',
                                'deploy_unit': '',
                                'executor': '张三',
                                'external_link': '',
                                'raw_data': {
                                    '任务名': '创建用户表',
                                    '操作类型': '新增',
                                    '执行人': '张三',
                                    '备注': '初始化脚本'
                                }
                            }
                        ]
                    },
                    {
                        'action_type': '删除',
                        'instruction': '【高危操作】删除以下配置：',
                        'is_high_risk': True,
                        'tasks': [
                            {
                                'task_name': '删除临时表',
                                'deploy_unit': '',
                                'executor': '王五',
                                'external_link': '',
                                'raw_data': {
                                    '任务名': '删除临时表',
                                    '操作类型': '删除',
                                    '执行人': '王五',
                                    '备注': '清理废弃数据'
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
