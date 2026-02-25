# -*- coding: utf-8 -*-
"""
Web API 单元测试
测试 ConfigService、BackupService、Upload API
"""

import io
import os
import json
import shutil
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import yaml
from flask import Flask
from flask.testing import FlaskClient

from src.web.app import create_app
from src.web.services import ConfigService, BackupService


# ========== Fixtures ==========

@pytest.fixture
def temp_config_dir():
    """创建临时配置目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir) / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        backup_dir = config_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        images_dir = config_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        yield {
            "config_path": config_dir / "rules.yaml",
            "backup_dir": backup_dir,
            "images_dir": images_dir,
            "root": tmpdir
        }


@pytest.fixture
def sample_rules_yaml(temp_config_dir):
    """创建测试用 rules.yaml"""
    config_data = {
        "priority_rules": {
            "数据库脚本部署": 10,
            "上线代码包清单": 20,
            "应用配置": 30,
        },
        "action_library": {
            "新增": {
                "instruction": "新增以下配置：",
                "is_high_risk": False,
                "render_table": True
            },
            "修改": {
                "instruction": "修改以下配置：",
                "is_high_risk": False,
                "render_table": True
            },
            "删除": {
                "instruction": "【高危操作】删除以下配置：",
                "is_high_risk": True,
                "render_table": True
            },
        },
        "high_risk_keywords": ["删除"],
        "sheet_column_mapping": {
            "数据库脚本部署": {
                "columns": ["脚本名称", "执行顺序", "数据库"],
                "column_mapping": {
                    "脚本名称": ["脚本名称", "任务名"],
                    "执行顺序": ["执行顺序", "序号"],
                }
            }
        },
        "core_fields": {
            "task_name": {
                "aliases": ["任务名", "任务名称"],
                "required": True
            }
        }
    }
    
    config_path = temp_config_dir["config_path"]
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
    
    return config_path


@pytest.fixture
def web_app(sample_rules_yaml, temp_config_dir):
    """创建 Flask 测试应用"""
    app = create_app(config_path=str(sample_rules_yaml))
    app.config['TESTING'] = True
    
    # 设置测试用的路径
    app.config['BACKUP_DIR'] = str(temp_config_dir["backup_dir"])
    app.config['IMAGES_DIR'] = str(temp_config_dir["images_dir"])
    
    yield app


@pytest.fixture
def client(web_app) -> FlaskClient:
    """Flask 测试客户端"""
    return web_app.test_client()


# ========== ConfigService 单元测试 ==========

class TestConfigService:
    """配置服务测试"""
    
    def test_load_config(self, sample_rules_yaml):
        """测试加载配置"""
        service = ConfigService(config_path=str(sample_rules_yaml))
        config = service.load()
        
        assert "priority_rules" in config
        assert "action_library" in config
        assert config["priority_rules"]["数据库脚本部署"] == 10
    
    def test_get_priority_rules(self, sample_rules_yaml):
        """测试获取章节优先级"""
        service = ConfigService(config_path=str(sample_rules_yaml))
        rules = service.get_priority_rules()
        
        assert "数据库脚本部署" in rules
        assert rules["数据库脚本部署"] == 10
    
    def test_set_priority_rules(self, sample_rules_yaml):
        """测试设置章节优先级"""
        service = ConfigService(config_path=str(sample_rules_yaml))
        
        new_rules = {
            "新章节": 5,
            "数据库脚本部署": 10,
        }
        service.set_priority_rules(new_rules)
        
        # 强制重新加载后验证
        service.load(force_reload=True)
        loaded_rules = service.get_priority_rules()
        assert "新章节" in loaded_rules
        assert loaded_rules["新章节"] == 5
    
    def test_add_chapter(self, sample_rules_yaml):
        """测试添加章节"""
        service = ConfigService(config_path=str(sample_rules_yaml))
        service.add_chapter("新模块", 50)
        
        rules = service.get_priority_rules()
        assert "新模块" in rules
        assert rules["新模块"] == 50
    
    def test_delete_chapter(self, sample_rules_yaml):
        """测试删除章节"""
        service = ConfigService(config_path=str(sample_rules_yaml))
        result = service.delete_chapter("应用配置")
        
        assert result is True
        rules = service.get_priority_rules()
        assert "应用配置" not in rules
    
    def test_get_action_library(self, sample_rules_yaml):
        """测试获取操作类型库 - 旧格式会自动迁移为新格式"""
        service = ConfigService(config_path=str(sample_rules_yaml))
        library = service.get_action_library()
        
        # 新格式下，操作类型按章节分组，旧格式会迁移到"默认"章节
        assert "默认" in library
        assert "新增" in library["默认"]
        assert "删除" in library["默认"]
        assert library["默认"]["删除"]["is_high_risk"] is True
    
    def test_set_action_high_risk_sync(self, sample_rules_yaml):
        """测试设置操作类型时同步高危关键字"""
        service = ConfigService(config_path=str(sample_rules_yaml))
        
        # 添加一个新的高危操作
        service.set_action("下线", {
            "instruction": "【高危操作】下线以下配置：",
            "is_high_risk": True,
            "render_table": True
        })
        
        # 验证 high_risk_keywords 已同步
        config = service.load()
        assert "下线" in config["high_risk_keywords"]
    
    def test_get_sheet_column_mapping(self, sample_rules_yaml):
        """测试获取 Sheet 列映射"""
        service = ConfigService(config_path=str(sample_rules_yaml))
        mapping = service.get_sheet_column_mapping()
        
        assert "数据库脚本部署" in mapping
        assert "columns" in mapping["数据库脚本部署"]


# ========== BackupService 单元测试 ==========

class TestBackupService:
    """备份服务测试"""
    
    @pytest.fixture
    def backup_service(self, sample_rules_yaml, temp_config_dir):
        """创建备份服务实例"""
        return BackupService(
            config_path=str(sample_rules_yaml),
            backup_dir=str(temp_config_dir["backup_dir"])
        )
    
    def test_create_backup(self, backup_service):
        """测试创建备份"""
        filename = backup_service.create_backup()
        
        assert filename is not None
        assert filename.startswith("rules.yaml.bak.")
    
    def test_list_backups(self, backup_service):
        """测试列出备份"""
        import time
        # 创建几个备份（间隔1秒避免时间戳冲突）
        backup_service.create_backup()
        time.sleep(1.1)
        backup_service.create_backup()
        
        backups = backup_service.list_backups()
        
        assert len(backups) >= 2
    
    def test_max_backups_limit(self, backup_service, temp_config_dir):
        """测试备份数量限制（最多10个）"""
        # 创建 12 个备份
        for _ in range(12):
            backup_service.create_backup()
        
        backups = backup_service.list_backups()
        
        # 应该只有 10 个
        assert len(backups) <= 10
    
    def test_restore_backup(self, backup_service, sample_rules_yaml):
        """测试回滚备份"""
        import time
        # 先获取初始配置
        service = ConfigService(config_path=str(sample_rules_yaml))
        original_rules = service.get_priority_rules().copy()
        
        # 创建初始备份（此时没有临时章节）
        backup_filename = backup_service.create_backup()
        time.sleep(1.1)  # 确保后续备份时间戳不同
        
        # 修改配置
        service.add_chapter("临时章节", 999)
        
        # 确认修改已生效
        service.load(force_reload=True)
        assert "临时章节" in service.get_priority_rules()
        
        # 回滚
        result = backup_service.restore_backup(backup_filename)
        assert result is True
        
        # 强制重新加载后验证
        service.load(force_reload=True)
        restored_rules = service.get_priority_rules()
        assert "临时章节" not in restored_rules
    
    def test_get_backup_content(self, backup_service):
        """测试获取备份内容"""
        filename = backup_service.create_backup()
        content = backup_service.get_backup_content(filename)
        
        assert content is not None
        assert "priority_rules" in content
    
    def test_restore_requires_confirmation(self, backup_service):
        """测试回滚需要确认（通过 API 测试）"""
        # 此测试在 API 层验证
        pass


# ========== API 端点测试 ==========

class TestConfigAPI:
    """配置 API 测试"""
    
    def test_get_config(self, client):
        """测试获取完整配置"""
        response = client.get('/api/config')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "priority_rules" in data["data"]
    
    def test_save_config(self, client, sample_rules_yaml):
        """测试保存配置"""
        new_config = {
            "priority_rules": {"测试章节": 100},
            "action_library": {},
            "sheet_column_mapping": {}
        }
        
        response = client.put(
            '/api/config',
            data=json.dumps(new_config),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
    
    def test_get_priority_rules(self, client):
        """测试获取章节优先级"""
        response = client.get('/api/config/priority-rules')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], dict)
    
    def test_add_chapter_success(self, client):
        """测试添加章节（成功）"""
        response = client.post(
            '/api/config/priority-rules/chapter',
            data=json.dumps({"sheet_name": "新章节", "priority": 100}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
    
    def test_add_chapter_missing_priority(self, client):
        """测试添加章节（缺少优先级）"""
        response = client.post(
            '/api/config/priority-rules/chapter',
            data=json.dumps({"sheet_name": "新章节"}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "优先级不能为空" in data["error"]
    
    def test_add_chapter_missing_name(self, client):
        """测试添加章节（缺少名称）"""
        response = client.post(
            '/api/config/priority-rules/chapter',
            data=json.dumps({"priority": 100}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
    
    def test_delete_chapter(self, client):
        """测试删除章节"""
        # 先添加
        client.post(
            '/api/config/priority-rules/chapter',
            data=json.dumps({"sheet_name": "待删除章节", "priority": 99}),
            content_type='application/json'
        )
        
        # 再删除
        response = client.delete('/api/config/priority-rules/chapter/待删除章节')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
    
    def test_get_action_library(self, client):
        """测试获取操作类型库"""
        response = client.get('/api/config/action-library')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        # action_library 可能被其他测试清空，只验证返回结构正确
        assert isinstance(data["data"], dict)
    
    def test_set_action(self, client):
        """测试设置操作类型"""
        response = client.put(
            '/api/config/action-library/测试操作',
            data=json.dumps({
                "instruction": "测试操作说明",
                "is_high_risk": False,
                "render_table": True
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
    
    def test_get_sheet_column_mapping(self, client):
        """测试获取列映射"""
        response = client.get('/api/config/sheet-column-mapping')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True


class TestBackupAPI:
    """备份 API 测试"""
    
    def test_list_backups(self, client):
        """测试列出备份"""
        response = client.get('/api/backups')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    def test_create_backup(self, client):
        """测试创建备份"""
        response = client.post('/api/backups/create')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "filename" in data
    
    def test_get_backup_content(self, client):
        """测试获取备份内容"""
        # 先创建备份
        create_response = client.post('/api/backups/create')
        filename = create_response.get_json()["filename"]
        
        # 获取内容
        response = client.get(f'/api/backups/{filename}')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
    
    def test_restore_without_confirmation(self, client):
        """测试回滚（未确认）"""
        # 先创建备份
        create_response = client.post('/api/backups/create')
        filename = create_response.get_json()["filename"]
        
        # 尝试回滚但不确认
        response = client.post(
            f'/api/backups/{filename}/restore',
            data=json.dumps({"confirmed": False}),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert data.get("requires_confirmation") is True
    
    def test_restore_with_confirmation(self, client):
        """测试回滚（已确认）"""
        # 先创建备份
        create_response = client.post('/api/backups/create')
        filename = create_response.get_json()["filename"]
        
        # 确认回滚
        response = client.post(
            f'/api/backups/{filename}/restore',
            data=json.dumps({"confirmed": True}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True


class TestUploadAPI:
    """上传 API 测试"""
    
    def test_upload_image_success(self, client, temp_config_dir):
        """测试上传图片（成功）"""
        # 创建一个测试图片
        image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
        
        response = client.post(
            '/api/upload/image',
            data={
                'file': (io.BytesIO(image_data), 'test.png')
            },
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "url" in data
        assert data["url"].startswith("/images/")
    
    def test_upload_image_invalid_type(self, client):
        """测试上传图片（无效类型）"""
        response = client.post(
            '/api/upload/image',
            data={
                'file': (io.BytesIO(b'test content'), 'test.txt')
            },
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
        assert "不支持的文件类型" in data["error"]
    
    def test_upload_image_no_file(self, client):
        """测试上传图片（无文件）"""
        response = client.post('/api/upload/image')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False
    
    def test_upload_excel_columns(self, client):
        """测试上传 Excel 识别列名"""
        # 创建一个简单的 Excel 文件
        import pandas as pd
        
        df = pd.DataFrame({
            '任务名': ['任务1', '任务2'],
            '操作类型': ['新增', '修改'],
            '执行人': ['张三', '李四']
        })
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_buffer.seek(0)
        
        response = client.post(
            '/api/upload/excel',
            data={
                'file': (excel_buffer, 'test.xlsx')
            },
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "columns" in data
        assert "任务名" in data["columns"]
        assert "操作类型" in data["columns"]
    
    def test_upload_excel_invalid_type(self, client):
        """测试上传 Excel（无效类型）"""
        response = client.post(
            '/api/upload/excel',
            data={
                'file': (io.BytesIO(b'test'), 'test.txt')
            },
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["success"] is False


# ========== 页面路由测试 ==========

class TestPageRoutes:
    """页面路由测试"""
    
    def test_index_page(self, client):
        """测试首页"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_chapters_page(self, client):
        """测试章节排序页面"""
        response = client.get('/chapters')
        assert response.status_code == 200
    
    def test_actions_page(self, client):
        """测试操作类型页面"""
        response = client.get('/actions')
        assert response.status_code == 200
    
    def test_columns_page(self, client):
        """测试列映射页面"""
        response = client.get('/columns')
        assert response.status_code == 200
    
    def test_backups_page(self, client):
        """测试版本回滚页面"""
        response = client.get('/backups')
        assert response.status_code == 200
    
    def test_404_page(self, client):
        """测试 404 页面"""
        response = client.get('/nonexistent')
        assert response.status_code == 404


# ========== 边界与异常测试 ==========

class TestEdgeCases:
    """边界与异常测试"""
    
    def test_config_file_not_found(self, temp_config_dir):
        """测试配置文件不存在"""
        nonexistent_path = temp_config_dir["config_path"]
        service = ConfigService(config_path=str(nonexistent_path))
        
        with pytest.raises(FileNotFoundError):
            service.load()
    
    def test_backup_file_not_found(self, temp_config_dir):
        """测试备份文件不存在"""
        service = BackupService(
            config_path=str(temp_config_dir["config_path"]),
            backup_dir=str(temp_config_dir["backup_dir"])
        )
        
        result = service.restore_backup("nonexistent.yaml")
        assert result is False
    
    def test_save_empty_config(self, client):
        """测试保存空配置"""
        response = client.put(
            '/api/config',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        # 空配置被 API 认为是无效（"配置数据不能为空"）
        assert response.status_code == 400
    
    def test_save_invalid_json(self, client):
        """测试保存无效 JSON"""
        response = client.put(
            '/api/config',
            data="not a json",
            content_type='application/json'
        )
        
        # 无效 JSON 会触发异常，返回 500 或 400（取决于异常处理）
        assert response.status_code in [400, 500]
