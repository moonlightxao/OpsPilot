# -*- coding: utf-8 -*-
"""
V5 阶段测试：Excel 一键保存全量覆盖模式

测试用例：
- V5-T1: 验证 sheet_column_mapping 全量覆盖
- V5-T2: 鎟有配置被正确删除
- V5-T3: action_library 保持不变
- V5-T4: priority_rules 按 Sheet 顺序分配
- V5-T5: core_fields 全量重新生成
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from src.web.services.config_service import ConfigService


@pytest.fixture
def temp_config_path(tmp_path):
    """创建临时配置文件"""
    config_content = """
# ============================================================
# OpsPilot 规则配置文件
# ============================================================

priority_rules:
  OldSheet1: 10
  OldSheet2: 20
  应用配置: 30

action_library:
  默认:
    测试操作:
      instruction: 测试操作说明
      is_high_risk: false
      render_table: true
  应用配置:
    新增:
      instruction: 在应用配置中心新增配置
      is_high_risk: false
      render_table: true

sheet_column_mapping:
  OldSheet1:
    columns:
    - 操作类型
    - 部署单元
    column_mapping:
      操作类型:
      - 操作类型
      鸃署单元:
      - 部署单元
  OldSheet2:
    columns:
    - 任务名
    - 执行人
    column_mapping:
      任务名:
      - 任务名
      执行人:
      - 执行人
  应用配置:
    columns:
    - 操作类型
    - 键
    - 值
    column_mapping:
      操作类型:
      - 操作类型
      键:
      - 键
      值:
      - 值

core_fields:
  action_type:
    aliases:
      - 操作类型
      - 操作
    required: true
  deploy_unit:
    aliases:
      - 部署单元
      - 应用名
    required: false
  OldCustomField:
    aliases:
      - 旧自定义字段
    required: false
    custom: true
  AnotherOldField:
    aliases:
      - 另一个旧字段
    required: false
    custom: true

high_risk_keywords: []
"""
    config_file = tmp_path / "rules.yaml"
    config_file.write_text(config_content, encoding='utf-8')
    return config_file


@pytest.fixture
def config_service(temp_config_path):
    """创建使用临时配置的 ConfigService"""
    return ConfigService(str(temp_config_path))


class TestBatchSaveV5:
    """V5 阶段测试类"""

    def test_v5_t1_sheet_column_mapping_full_replace(self, config_service):
        """
        V5-T1: 验证 sheet_column_mapping 全量覆盖

        场景：
        - 原有配置包含 OldSheet1, OldSheet2, 应用配置
        - 上传 Excel 包含 SheetA, SheetB. SheetC
        - 期望：sheet_column_mapping 仅包含 SheetA. SheetB. SheetC
        """
        sheets = [
            {"name": "SheetA", "columns": ["操作类型", "部署单元"], "is_first_sheet": True},
            {"name": "SheetB", "columns": ["任务名", "执行人"], "is_first_sheet": False},
            {"name": "SheetC", "columns": ["参数", "值"], "is_first_sheet": False}
        ]

        result = config_service.batch_save_sheets(sheets)

        # 验证 updated 返回值
        assert "updated" in result
        assert set(result["updated"]["sheet_column_mapping"]) == {"SheetA", "SheetB", "SheetC"}

        # 验证配置文件中的 sheet_column_mapping
        config = config_service.load()
        assert set(config["sheet_column_mapping"].keys()) == {"SheetA", "SheetB", "SheetC"}

        # 验证列映射内容正确
        assert config["sheet_column_mapping"]["SheetA"]["columns"] == ["操作类型", "部署单元"]
        assert config["sheet_column_mapping"]["SheetB"]["columns"] == ["任务名", "执行人"]
        assert config["sheet_column_mapping"]["SheetC"]["columns"] == ["参数", "值"]

    def test_v5_t2_deleted_sheets_removed(self, config_service):
        """
        V5-T2: 原有配置被正确删除

        场景：
        - 原有配置包含 OldSheet1. OldSheet2. 应用配置
        - 上传 Excel 包含 SheetA. SheetB. SheetC（不包含 OldSheet1, OldSheet2）
        - 期望：OldSheet1, OldSheet2 从配置中删除
        """
        sheets = [
            {"name": "SheetA", "columns": ["操作类型"], "is_first_sheet": True},
            {"name": "SheetB", "columns": ["任务名"], "is_first_sheet": False},
            {"name": "SheetC", "columns": ["参数"], "is_first_sheet": False}
        ]

        result = config_service.batch_save_sheets(sheets)

        # 验证 deleted 返回值
        assert "deleted" in result
        assert "OldSheet1" in result["deleted"]["sheet_column_mapping"]
        assert "OldSheet2" in result["deleted"]["sheet_column_mapping"]
        assert "OldSheet1" in result["deleted"]["priority_rules"]
        assert "OldSheet2" in result["deleted"]["priority_rules"]

        # 验证配置文件中已删除
        config = config_service.load()
        assert "OldSheet1" not in config["sheet_column_mapping"]
        assert "OldSheet2" not in config["sheet_column_mapping"]
        assert "OldSheet1" not in config["priority_rules"]
        assert "OldSheet2" not in config["priority_rules"]

    def test_v5_t3_action_library_unchanged(self, config_service):
        """
        V5-T3: 验证 action_library 保持不变

        场景：
        - 原有 action_library 包含「默认/测试操作」和「应用配置/新增」
        - 执行 batch_save_sheets
        - 期望：action_library 保持不变
        """
        # 获取原始 action_library
        original_library = config_service.get_action_library()
        original_default_test = original_library.get("默认", {}).get("测试操作")
        original_app_new = original_library.get("应用配置", {}).get("新增")

        # 执行保存
        sheets = [
            {"name": "NewSheet", "columns": ["操作类型"], "is_first_sheet": True}
        ]
        config_service.batch_save_sheets(sheets)

        # 验证 action_library 未被修改
        new_library = config_service.get_action_library()
        assert new_library.get("默认", {}).get("测试操作") == original_default_test
        assert new_library.get("应用配置", {}).get("新增") == original_app_new

    def test_v5_t4_priority_rules_sequential(self, config_service):
        """
        V5-T4: 验证 priority_rules 按 Sheet 顺序分配（10, 20, 30...）

        场景：
        - 上传 Excel 包含 SheetA（第一个）, SheetB, SheetC, SheetD
        - 期望：priority_rules 为 {SheetB: 10, SheetC: 20, SheetD: 30}
        """
        sheets = [
            {"name": "SheetA", "columns": ["操作类型"], "is_first_sheet": True},
            {"name": "SheetB", "columns": ["任务名"], "is_first_sheet": False},
            {"name": "SheetC", "columns": ["参数"], "is_first_sheet": False},
            {"name": "SheetD", "columns": ["值"], "is_first_sheet": False}
        ]

        result = config_service.batch_save_sheets(sheets)

        # 验证 priority_rules
        config = config_service.load()
        priority_rules = config["priority_rules"]

        # 第一个 Sheet 不在 priority_rules 中
        assert "SheetA" not in priority_rules

        # 其他 Sheet 按顺序分配优先级
        assert priority_rules["SheetB"] == 10
        assert priority_rules["SheetC"] == 20
        assert priority_rules["SheetD"] == 30

    def test_v5_t5_core_fields_full_regenerate(self, config_service):
        """
        V5-T5: 验证 core_fields 基于新列名重新生成，旧字段被清理

        场景：
        - 原有 core_fields 包含预置字段和自定义字段 OldCustomField, AnotherOldField
        - 上传 Excel 包含列：操作类型、 部署单元、 任务名、 新自定义列
        - 期望：
          - 预置字段保留（aliases 基于新列名重新生成）
          - 自定义字段 OldCustomField, AnotherOldField 被删除
          - 新自定义列「新自定义列」被创建
        """
        sheets = [
            {"name": "Sheet1", "columns": ["操作类型", "部署单元", "任务名", "新自定义列"], "is_first_sheet": True}
        ]

        result = config_service.batch_save_sheets(sheets)

        # 验证 deleted 返回值包含旧自定义字段
        assert "deleted" in result
        assert "OldCustomField" in result["deleted"]["core_fields"]
        assert "AnotherOldField" in result["deleted"]["core_fields"]

        # 验证配置文件中的 core_fields
        config = config_service.load()
        core_fields = config["core_fields"]

        # 预置字段应保留
        assert "action_type" in core_fields
        assert "deploy_unit" in core_fields
        assert "task_name" in core_fields

        # 预置字段的 aliases 应基于新列名重新生成
        assert "操作类型" in core_fields["action_type"]["aliases"]
        assert "部署单元" in core_fields["deploy_unit"]["aliases"]
        assert "任务名" in core_fields["task_name"]["aliases"]

        # 旧自定义字段应被删除
        assert "OldCustomField" not in core_fields
        assert "AnotherOldField" not in core_fields

        # 新自定义列应被创建
        assert "新自定义列" in core_fields
        assert core_fields["新自定义列"]["custom"] == True
