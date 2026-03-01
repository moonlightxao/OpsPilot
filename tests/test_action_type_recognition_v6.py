# -*- coding: utf-8 -*-
"""
V6 阶段测试：Excel 导入自动识别操作类型

测试用例：
- V6-T1: 操作类型列识别逻辑
- V6-T2: 批量保存 API（新增、覆盖、跳过场景）
- V6-T3: 无操作类型列的 Sheet 跳过处理
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.web.services.config_service import ConfigService
from src.web.routes.upload import _find_action_type_column


@pytest.fixture
def temp_config_path(tmp_path):
    """创建临时配置文件"""
    config_content = """
# ============================================================
# OpsPilot 规则配置文件
# ============================================================

priority_rules:
  ROMA任务: 10

action_library:
  ROMA任务:
    新增:
      instruction: 新增任务
      is_high_risk: false
      render_table: true

core_fields:
  action_type:
    aliases:
      - 操作类型
      - 操作
      - action
      - Operation
    required: true
  deploy_unit:
    aliases:
      - 部署单元
      - 应用名
    required: false

sheet_column_mapping:
  ROMA任务:
    columns:
      - 任务名
      - 操作类型
      - 执行人
    column_mapping:
      任务名:
        - 任务名
      操作类型:
        - 操作类型
      执行人:
        - 执行人

high_risk_keywords: []
"""
    config_file = tmp_path / "rules.yaml"
    config_file.write_text(config_content, encoding='utf-8')
    return config_file


@pytest.fixture
def config_service(temp_config_path):
    """创建使用临时配置的 ConfigService"""
    return ConfigService(str(temp_config_path))


class TestActionTypeRecognitionV6:
    """V6 阶段测试类"""

    def test_v6_t1_find_action_type_column(self):
        """
        V6-T1: 操作类型列识别逻辑

        验证 _find_action_type_column 函数能正确识别操作类型列
        """
        aliases = ["操作类型", "操作", "action", "Operation"]

        # 测试标准匹配
        columns1 = ["任务名", "操作类型", "执行人"]
        result1 = _find_action_type_column(columns1, aliases)
        assert result1 == "操作类型", f"应识别到 '操作类型'，实际: {result1}"

        # 测试别名匹配（包含"操作"关键词）
        columns2 = ["任务名称", "具体操作", "负责人"]
        result2 = _find_action_type_column(columns2, aliases)
        assert result2 == "具体操作", f"应识别到 '具体操作'，实际: {result2}"

        # 测试英文匹配
        columns3 = ["Task Name", "Operation Type", "Executor"]
        result3 = _find_action_type_column(columns3, aliases)
        assert result3 == "Operation Type", f"应识别到 'Operation Type'，实际: {result3}"

        # 测试无匹配
        columns4 = ["任务名", "执行人", "复核人"]
        result4 = _find_action_type_column(columns4, aliases)
        assert result4 is None, f"无匹配时应返回 None，实际: {result4}"

        # 测试大小写不敏感
        columns5 = ["任务", "ACTION", "人员"]
        result5 = _find_action_type_column(columns5, aliases)
        assert result5 == "ACTION", f"应识别到 'ACTION'，实际: {result5}"

    def test_v6_t2_batch_save_action_types(self, config_service):
        """
        V6-T2: 批量保存 API（新增、覆盖、跳过场景）

        场景：
        1. 新增操作类型
        2. 覆盖已存在的操作类型
        3. 跳过已存在的操作类型
        """
        # 初始状态：ROMA任务 已有「新增」操作类型

        # 场景1: 新增操作类型
        action_types = {
            "ROMA任务": {
                "删除": {"overwrite": False},
                "修改": {"overwrite": False}
            }
        }
        result = config_service.batch_save_action_types(action_types)

        assert "ROMA任务" in result["added"]
        assert "删除" in result["added"]["ROMA任务"]
        assert "修改" in result["added"]["ROMA任务"]

        # 验证配置已保存
        library = config_service.get_action_library()
        assert "删除" in library["ROMA任务"]
        assert "修改" in library["ROMA任务"]
        assert library["ROMA任务"]["删除"]["instruction"] == "删除"
        assert library["ROMA任务"]["删除"]["is_high_risk"] == False

        # 场景2: 跳过已存在的操作类型（不覆盖）
        action_types2 = {
            "ROMA任务": {
                "删除": {"overwrite": False}  # 已存在，不覆盖
            }
        }
        result2 = config_service.batch_save_action_types(action_types2)

        assert "ROMA任务" in result2["skipped"]
        assert "删除" in result2["skipped"]["ROMA任务"]

        # 场景3: 覆盖已存在的操作类型
        action_types3 = {
            "ROMA任务": {
                "删除": {"overwrite": True}  # 已存在，覆盖
            }
        }
        result3 = config_service.batch_save_action_types(action_types3)

        assert "ROMA任务" in result3["updated"]
        assert "删除" in result3["updated"]["ROMA任务"]

        # 场景4: 新章节（之前不存在的章节）
        action_types4 = {
            "新章节": {
                "新增": {"overwrite": False}
            }
        }
        result4 = config_service.batch_save_action_types(action_types4)

        assert "新章节" in result4["added"]
        assert "新增" in result4["added"]["新章节"]

        library2 = config_service.get_action_library()
        assert "新章节" in library2
        assert "新增" in library2["新章节"]

    def test_v6_t3_skip_sheet_without_action_type_column(self, config_service):
        """
        V6-T3: 无操作类型列的 Sheet 跳过处理

        验证：如果 Sheet 没有操作类型列，在保存操作类型时应跳过
        """
        # 模拟场景：有一个没有操作类型的 Sheet
        # 由于 batch_save_action_types 接收的是已经识别好的数据
        # 如果传入空对象，应该能正确处理

        action_types = {
            "无操作类型Sheet": {}  # 没有识别到任何操作类型
        }

        # 应该不会报错
        result = config_service.batch_save_action_types(action_types)

        # 没有任何操作类型需要保存
        assert result["added"] == {} or "无操作类型Sheet" not in result["added"]

    def test_v6_default_attributes(self, config_service):
        """
        验证操作类型默认属性正确填充

        新增的操作类型应有以下默认属性：
        - instruction = 操作类型名
        - is_high_risk = false
        - render_table = true
        """
        action_types = {
            "测试章节": {
                "测试操作": {"overwrite": False}
            }
        }

        config_service.batch_save_action_types(action_types)

        library = config_service.get_action_library()
        action_config = library["测试章节"]["测试操作"]

        assert action_config["instruction"] == "测试操作"
        assert action_config["is_high_risk"] == False
        assert action_config["render_table"] == True
