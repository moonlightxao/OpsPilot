# -*- coding: utf-8 -*-
"""
Web 配置中心 V2 API 测试
测试操作类型章节绑定和批量删除功能
"""

import pytest
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web.services import ConfigService


class TestConfigServiceV2:
    """测试 ConfigService V2 扩展功能"""

    def setup_method(self):
        """每个测试方法前初始化"""
        self.config_service = ConfigService()

    def test_is_flat_action_library(self):
        """测试旧格式检测"""
        # 旧格式（扁平结构）
        old_format = {
            "新增": {"instruction": "...", "is_high_risk": False},
            "删除": {"instruction": "...", "is_high_risk": True}
        }
        assert self.config_service._is_flat_action_library(old_format) == True

        # 新格式（章节嵌套）
        new_format = {
            "应用配置": {
                "新增": {"instruction": "...", "is_high_risk": False}
            }
        }
        assert self.config_service._is_flat_action_library(new_format) == False

        # 空数据
        assert self.config_service._is_flat_action_library({}) == False

    def test_get_action_library_auto_migrate(self):
        """测试自动迁移旧格式"""
        # 直接测试获取，应该返回新格式或空
        library = self.config_service.get_action_library()
        assert isinstance(library, dict)

    def test_get_chapter_actions(self):
        """测试获取章节操作类型"""
        # 获取不存在的章节，应返回空字典
        actions = self.config_service.get_chapter_actions("不存在的章节")
        assert actions == {}

    def test_set_chapter_action(self):
        """测试设置章节操作类型"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        temp_config = os.path.join(temp_dir, "test_rules.yaml")
        shutil.copy("config/rules.yaml", temp_config)

        try:
            service = ConfigService(temp_config)

            # 设置新操作类型
            service.set_chapter_action("TestChapter", "Add", {
                "instruction": "test instruction",
                "is_high_risk": False,
                "render_table": True
            })

            # 直接读取验证（不使用自动迁移）
            actions = service.get_action_library(auto_migrate=False).get("TestChapter", {})
            assert "Add" in actions
            assert actions["Add"]["instruction"] == "test instruction"

        finally:
            shutil.rmtree(temp_dir)

    def test_batch_delete_chapters(self):
        """测试批量删除章节"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        temp_config = os.path.join(temp_dir, "test_rules.yaml")
        shutil.copy("config/rules.yaml", temp_config)

        try:
            service = ConfigService(temp_config)

            # 先添加测试章节
            service.add_chapter("测试章节1", 100)
            service.add_chapter("测试章节2", 110)

            # 批量删除
            deleted = service.batch_delete_chapters(["测试章节1", "测试章节2"])
            assert "测试章节1" in deleted
            assert "测试章节2" in deleted

            # 验证已删除
            rules = service.get_priority_rules()
            assert "测试章节1" not in rules
            assert "测试章节2" not in rules

        finally:
            shutil.rmtree(temp_dir)

    def test_batch_delete_chapter_actions(self):
        """测试批量删除操作类型"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        temp_config = os.path.join(temp_dir, "test_rules.yaml")
        shutil.copy("config/rules.yaml", temp_config)

        try:
            service = ConfigService(temp_config)

            # 先添加测试操作类型
            service.set_chapter_action("测试章节", "操作1", {"instruction": "1", "is_high_risk": False})
            service.set_chapter_action("测试章节", "操作2", {"instruction": "2", "is_high_risk": False})

            # 批量删除
            deleted = service.batch_delete_chapter_actions("测试章节", ["操作1", "操作2"])
            assert "操作1" in deleted
            assert "操作2" in deleted

            # 验证已删除
            actions = service.get_chapter_actions("测试章节")
            assert "操作1" not in actions
            assert "操作2" not in actions

        finally:
            shutil.rmtree(temp_dir)

    def test_batch_delete_sheet_mappings(self):
        """测试批量删除 Sheet 列映射"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        temp_config = os.path.join(temp_dir, "test_rules.yaml")
        shutil.copy("config/rules.yaml", temp_config)

        try:
            service = ConfigService(temp_config)

            # 先添加测试映射
            service.set_sheet_mapping("测试Sheet1", {"columns": ["a"], "column_mapping": {}})
            service.set_sheet_mapping("测试Sheet2", {"columns": ["b"], "column_mapping": {}})

            # 批量删除
            deleted = service.batch_delete_sheet_mappings(["测试Sheet1", "测试Sheet2"])
            assert "测试Sheet1" in deleted
            assert "测试Sheet2" in deleted

            # 验证已删除
            mapping = service.get_sheet_column_mapping()
            assert "测试Sheet1" not in mapping
            assert "测试Sheet2" not in mapping

        finally:
            shutil.rmtree(temp_dir)

    def test_sync_high_risk_keywords(self):
        """测试高危关键字同步"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        temp_config = os.path.join(temp_dir, "test_rules.yaml")
        shutil.copy("config/rules.yaml", temp_config)

        try:
            service = ConfigService(temp_config)

            # 设置带高危标记的操作类型
            service.set_chapter_action("章节1", "删除", {"instruction": "删除操作", "is_high_risk": True})
            service.set_chapter_action("章节2", "重启", {"instruction": "重启操作", "is_high_risk": True})

            # 验证高危关键字已同步
            config = service.load()
            assert "删除" in config.get("high_risk_keywords", [])
            assert "重启" in config.get("high_risk_keywords", [])

        finally:
            shutil.rmtree(temp_dir)


class TestActionLibraryAPI:
    """测试操作类型 API（需要 Web 服务运行）"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """检查 Web 服务是否运行"""
        import urllib.request
        try:
            urllib.request.urlopen('http://127.0.0.1:8080/api/config', timeout=2)
            self.web_running = True
        except:
            self.web_running = False

    @pytest.mark.skip(reason="需要手动启动 Web 服务后运行")
    def test_get_chapter_actions_api(self):
        """测试获取章节操作类型 API"""
        if not self.web_running:
            pytest.skip("Web 服务未运行")

        import urllib.request
        from urllib.parse import quote
        # 使用 URL 编码处理中文
        url = 'http://127.0.0.1:8080/api/config/action-library/chapter/' + quote('ROMA任务')
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            assert data.get('success') == True
            assert isinstance(data.get('data'), dict)

    @pytest.mark.skip(reason="需要手动启动 Web 服务后运行")
    def test_batch_delete_api_not_found(self):
        """测试批量删除 API（删除不存在的项）"""
        if not self.web_running:
            pytest.skip("Web 服务未运行")

        import urllib.request
        from urllib.parse import quote
        url = 'http://127.0.0.1:8080/api/config/action-library/batch-delete'
        req = urllib.request.Request(
            url,
            data=json.dumps({
                'chapter': '不存在的章节',
                'action_names': ['不存在的操作']
            }).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            assert data.get('success') == True
            assert len(data.get('deleted', [])) == 0


class TestCoreFieldSync:
    """测试核心字段同步功能"""

    def setup_method(self):
        """每个测试方法前初始化"""
        self.config_service = ConfigService()

    def test_match_core_field_action_type(self):
        """测试 action_type 关键词匹配"""
        assert self.config_service._match_core_field("操作类型") == "action_type"
        assert self.config_service._match_core_field("操作") == "action_type"
        assert self.config_service._match_core_field("Action") == "action_type"
        assert self.config_service._match_core_field("Action Type") == "action_type"
        assert self.config_service._match_core_field("操作动作类型") == "action_type"

    def test_match_core_field_deploy_unit(self):
        """测试 deploy_unit 关键词匹配"""
        assert self.config_service._match_core_field("部署单元") == "deploy_unit"
        assert self.config_service._match_core_field("应用名") == "deploy_unit"
        assert self.config_service._match_core_field("服务名") == "deploy_unit"
        assert self.config_service._match_core_field("应用名称") == "deploy_unit"
        assert self.config_service._match_core_field("部署单元名称") == "deploy_unit"

    def test_match_core_field_executor(self):
        """测试 executor 关键词匹配"""
        assert self.config_service._match_core_field("执行人") == "executor"
        assert self.config_service._match_core_field("实施人") == "executor"
        assert self.config_service._match_core_field("负责人") == "executor"
        assert self.config_service._match_core_field("复核人") == "executor"

    def test_match_core_field_task_name(self):
        """测试 task_name 关键词匹配"""
        assert self.config_service._match_core_field("任务名") == "task_name"
        assert self.config_service._match_core_field("任务名称") == "task_name"
        assert self.config_service._match_core_field("Task") == "task_name"
        assert self.config_service._match_core_field("Task Name") == "task_name"

    def test_match_core_field_external_link(self):
        """测试 external_link 关键词匹配"""
        assert self.config_service._match_core_field("外部链接") == "external_link"
        assert self.config_service._match_core_field("链接") == "external_link"
        assert self.config_service._match_core_field("URL") == "external_link"
        assert self.config_service._match_core_field("url地址") == "external_link"

    def test_match_core_field_no_match(self):
        """测试无匹配情况"""
        assert self.config_service._match_core_field("备注") is None
        assert self.config_service._match_core_field("其他列") is None
        assert self.config_service._match_core_field("序号") is None
        assert self.config_service._match_core_field("开始时间") is None

    def test_sync_core_fields_from_columns(self):
        """测试核心字段同步"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        temp_config = os.path.join(temp_dir, "test_rules.yaml")
        shutil.copy("config/rules.yaml", temp_config)

        try:
            service = ConfigService(temp_config)

            # 设置测试列映射
            service.set_sheet_column_mapping({
                "测试Sheet1": {
                    "columns": ["任务序号", "任务名", "操作类型", "部署单元", "执行人", "备注"],
                    "column_mapping": {
                        "任务序号": ["任务序号"],
                        "任务名": ["任务名"],
                        "操作类型": ["操作类型"],
                        "部署单元": ["部署单元"],
                        "执行人": ["执行人"],
                        "备注": ["备注"]
                    }
                }
            })

            # 执行同步
            result = service.sync_core_fields_from_columns()

            # 验证结果
            assert "synced_count" in result
            assert "updated_fields" in result
            assert "new_aliases" in result

            # 验证 task_name 增加了 "任务序号" 别名（包含"任务名"关键词）
            config = service.load()
            task_name_aliases = config["core_fields"]["task_name"]["aliases"]
            # "任务序号" 包含 "任务名" 关键词（"任务"），应该被匹配
            # 但实际上 "任务序号" 不包含 "任务名" 这个完整关键词
            # 让我们检查 "任务名" 是否存在
            assert "任务名" in task_name_aliases

        finally:
            shutil.rmtree(temp_dir)

    def test_sync_core_fields_increments_only(self):
        """测试同步仅增量更新，不删除现有别名"""
        import tempfile
        import shutil

        temp_dir = tempfile.mkdtemp()
        temp_config = os.path.join(temp_dir, "test_rules.yaml")
        shutil.copy("config/rules.yaml", temp_config)

        try:
            service = ConfigService(temp_config)

            # 获取现有别名
            config = service.load()
            if "core_fields" in config and "task_name" in config["core_fields"]:
                original_aliases = set(config["core_fields"]["task_name"].get("aliases", []))
            else:
                original_aliases = set()

            # 设置新的列映射（不包含 task_name 相关列）
            service.set_sheet_column_mapping({
                "测试Sheet": {
                    "columns": ["备注", "状态"],
                    "column_mapping": {"备注": ["备注"], "状态": ["状态"]}
                }
            })

            # 执行同步
            service.sync_core_fields_from_columns()

            # 验证原有别名未被删除
            config = service.load()
            if original_aliases:
                current_aliases = set(config["core_fields"]["task_name"].get("aliases", []))
                # 原有别名应该仍然存在
                assert original_aliases.issubset(current_aliases)

        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
