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
        'implementation_summary': {
            'strategy': 'first_sheet',
            'sheet_names': ['上线安排', '实施总表'],
            'output_columns': ['序号', '任务', '开始时间', '结束时间', '实施人', '复核人'],
            'column_mapping': {
                '任务': ['任务名', '任务名称', '任务', 'Task'],
                '开始时间': ['开始时间', '开始日期', '计划开始'],
                '结束时间': ['结束时间', '结束日期', '计划结束'],
                '实施人': ['实施人', '执行人', '负责人'],
                '复核人': ['复核人', '复核', '审核人'],
            },
            'date_columns': ['开始时间', '结束时间'],
            'auto_sequence': True,
            'drop_unnamed_columns': True,
        },
        'priority_rules': {
            "数据库脚本部署": 10,
            "上线代码包清单": 15,
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
                'columns': ["脚本名称", "执行顺序", "数据库", "执行人", "备注"],
                'column_mapping': {
                    "脚本名称": ["脚本名称", "任务名", "任务名称"],
                    "执行顺序": ["执行顺序", "序号", "#"],
                    "数据库": ["数据库", "库名", "目标库"],
                    "执行人": ["执行人", "负责人"],
                    "备注": ["备注", "说明"]
                }
            },
            "上线代码包清单": {
                'columns': ["包名", "包类型", "部署资源", "实施人", "备注"],
                'column_mapping': {
                    "包名": ["包名", "文件名", "名称"],
                    "包类型": ["包类型", "类型", "分类"],
                    "部署资源": ["部署资源名", "资源", "目标"],
                    "实施人": ["实施人", "执行人", "负责人"],
                    "备注": ["备注", "说明"]
                }
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
    """创建测试用 Excel 文件（同时包含 core_fields 和 sheet_column_mapping 列名）
    注意：第一个 Sheet 固定为实施总表（implementation_summary），不进入 sections
    """
    # Sheet 1: 上线安排（实施总表，strategy=first_sheet 时解析为该结构）
    df0 = pd.DataFrame({
        '阶段': ['准备', '部署', '验证'],
        '任务': ['环境检查', '脚本执行', '功能验证'],
        '负责人': ['张三', '李四', '王五'],
        '计划时间': ['09:00', '10:00', '11:00']
    })

    # Sheet 2: 数据库脚本部署
    df1 = pd.DataFrame({
        '任务名': ['创建用户表', '添加索引', '删除临时表'],
        '操作类型': ['新增', '新增', '删除'],
        '脚本名称': ['创建用户表', '添加索引', '删除临时表'],
        '执行顺序': ['1', '2', '3'],
        '数据库': ['user_db', 'order_db', 'temp_db'],
        '执行人': ['张三', '李四', '王五'],
        '备注': ['初始化脚本', '性能优化', '清理废弃数据']
    })

    # Sheet 3: 上线代码包清单（与 rules.yaml 配置一致）
    df2 = pd.DataFrame({
        '任务名': ['部署服务A', '升级服务B'],
        '操作类型': ['部署', '升级'],
        '包名': ['service-a-v1.0.0.jar', 'service-b-v2.0.0.jar'],
        '包类型': ['JAR', 'JAR'],
        '部署资源名': ['server-01', 'server-02'],
        '实施人': ['张三', '李四'],
        '备注': ['新服务', '版本升级']
    })

    excel_path = temp_dir / "test_checklist.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df0.to_excel(writer, sheet_name='上线安排', index=False)
        df1.to_excel(writer, sheet_name='数据库脚本部署', index=False)
        df2.to_excel(writer, sheet_name='上线代码包清单', index=False)

    return excel_path


@pytest.fixture
def sample_excel_with_high_risk(temp_dir):
    """创建包含高危操作的测试 Excel 文件
    第一个 Sheet 为实施总表占位，第二个 Sheet 为应用配置（含高危操作）
    """
    df0 = pd.DataFrame({'阶段': ['准备'], '任务': ['检查'], '负责人': ['张三']})
    df = pd.DataFrame({
        '任务名': ['删除用户数据', '下线服务C', '普通修改'],
        '操作类型': ['删除', '下线', '修改'],
        '执行人': ['张三', '李四', '王五'],
        '备注': ['高危操作', '高危操作', '普通操作']
    })

    excel_path = temp_dir / "test_high_risk.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df0.to_excel(writer, sheet_name='上线安排', index=False)
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
def excel_impl_summary_with_dates_and_unnamed(temp_dir):
    """实施总表含 Excel 日期序列号和 Unnamed 列，用于测试列映射与日期转换"""
    # 46315 ≈ 2026-10-14, 46316 ≈ 2026-10-15
    df0 = pd.DataFrame({
        '任务': ['任务A', '任务B'],
        'Unnamed: 1': ['应过滤', '应过滤'],
        '开始时间': [46315, 46316],
        '结束时间': [46316, 46317],
        '实施人': ['张三', '李四'],
        '复核人': ['王五', '赵六'],
    })
    df1 = pd.DataFrame({
        '任务名': ['脚本1'],
        '操作类型': ['新增'],
        '执行人': ['张三'],
        '备注': [''],
    })
    excel_path = temp_dir / "test_impl_dates.xlsx"
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df0.to_excel(writer, sheet_name='上线安排', index=False)
        df1.to_excel(writer, sheet_name='数据库脚本部署', index=False)
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
    """创建测试用 report.json 数据 (v2.0 格式: columns + cells)"""
    return {
        'meta': {
            'source_file': 'test_checklist.xlsx',
            'generated_at': '2026-02-18T10:00:00Z',
            'version': '2.0.0'
        },
        'summary': {
            'total_tasks': 3,
            'total_sheets': 1,
            'high_risk_count': 1,
            'has_external_links': False,
            'external_links': []
        },
        'has_risk_alerts': True,
        'risk_alerts': [
            {
                'sheet_name': '应用配置',
                'action_type': '删除',
                'task_count': 1,
                'task_names': ['删除临时表']
            }
        ],
        'implementation_summary': {
            'sheet_name': '',
            'columns': [],
            'rows': [],
            'has_data': False,
        },
        'sections': [
            {
                'section_name': '应用配置',
                'priority': 20,
                'has_action_groups': True,
                'columns': ['任务名', '操作类型', '执行人', '备注'],
                'task_count': 3,
                'action_groups': [
                    {
                        'action_type': '新增',
                        'instruction': '新增以下配置：',
                        'is_high_risk': False,
                        'task_count': 1,
                        'tasks': [
                            {'cells': ['创建用户表', '新增', '张三', '初始化脚本']}
                        ]
                    },
                    {
                        'action_type': '删除',
                        'instruction': '【高危操作】删除以下配置：',
                        'is_high_risk': True,
                        'task_count': 1,
                        'tasks': [
                            {'cells': ['删除临时表', '删除', '王五', '清理废弃数据']}
                        ]
                    }
                ]
            }
        ]
    }
