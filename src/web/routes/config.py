# -*- coding: utf-8 -*-
"""
配置路由 - 配置读写 API
"""

from flask import Blueprint, jsonify, request
from ..services import ConfigService

config_bp = Blueprint('config', __name__, url_prefix='/api/config')
config_service = ConfigService()


@config_bp.route('', methods=['GET'])
def get_config():
    """获取完整配置"""
    try:
        config = config_service.load()
        return jsonify({"success": True, "data": config})
    except FileNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('', methods=['PUT'])
def save_config():
    """保存完整配置"""
    try:
        config = request.get_json()
        if not config:
            return jsonify({"success": False, "error": "配置数据不能为空"}), 400

        # 创建备份（在保存前）
        from ..services import BackupService
        backup_service = BackupService()
        backup_service.create_backup()

        # 保存配置
        config_service.save(config)
        return jsonify({"success": True, "message": "配置保存成功"})
    except ValueError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== 章节优先级配置 ==========

@config_bp.route('/priority-rules', methods=['GET'])
def get_priority_rules():
    """获取章节优先级配置"""
    try:
        rules = config_service.get_priority_rules()
        return jsonify({"success": True, "data": rules})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/priority-rules', methods=['PUT'])
def set_priority_rules():
    """设置章节优先级配置"""
    try:
        rules = request.get_json()
        if not isinstance(rules, dict):
            return jsonify({"success": False, "error": "配置格式错误"}), 400

        # 创建备份
        from ..services import BackupService
        BackupService().create_backup()

        config_service.set_priority_rules(rules)
        return jsonify({"success": True, "message": "章节配置保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/priority-rules/chapter', methods=['POST'])
def add_chapter():
    """添加新章节"""
    try:
        data = request.get_json()
        sheet_name = data.get('sheet_name')
        priority = data.get('priority')

        if not sheet_name:
            return jsonify({"success": False, "error": "Sheet 名称不能为空"}), 400
        if priority is None:
            return jsonify({"success": False, "error": "优先级不能为空"}), 400

        config_service.add_chapter(sheet_name, int(priority))
        return jsonify({"success": True, "message": "章节添加成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/priority-rules/chapter/<path:sheet_name>', methods=['DELETE'])
def delete_chapter(sheet_name: str):
    """删除章节"""
    try:
        if config_service.delete_chapter(sheet_name):
            return jsonify({"success": True, "message": "章节删除成功"})
        return jsonify({"success": False, "error": "章节不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== 操作类型配置 ==========

@config_bp.route('/action-library', methods=['GET'])
def get_action_library():
    """获取操作类型配置"""
    try:
        library = config_service.get_action_library()
        return jsonify({"success": True, "data": library})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/action-library', methods=['PUT'])
def set_action_library():
    """设置操作类型配置"""
    try:
        library = request.get_json()
        if not isinstance(library, dict):
            return jsonify({"success": False, "error": "配置格式错误"}), 400

        # 创建备份
        from ..services import BackupService
        BackupService().create_backup()

        config_service.set_action_library(library)
        return jsonify({"success": True, "message": "操作类型配置保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/action-library/<path:action_name>', methods=['GET'])
def get_action(action_name: str):
    """获取单个操作类型配置"""
    try:
        action = config_service.get_action(action_name)
        if action:
            return jsonify({"success": True, "data": action})
        return jsonify({"success": False, "error": "操作类型不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/action-library/<path:action_name>', methods=['PUT'])
def set_action(action_name: str):
    """设置单个操作类型配置"""
    try:
        action_config = request.get_json()
        if not action_config:
            return jsonify({"success": False, "error": "配置数据不能为空"}), 400

        # 创建备份
        from ..services import BackupService
        BackupService().create_backup()

        config_service.set_action(action_name, action_config)
        return jsonify({"success": True, "message": "操作类型保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/action-library/<path:action_name>', methods=['DELETE'])
def delete_action(action_name: str):
    """删除操作类型"""
    try:
        if config_service.delete_action(action_name):
            return jsonify({"success": True, "message": "操作类型删除成功"})
        return jsonify({"success": False, "error": "操作类型不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== 列映射配置 ==========

@config_bp.route('/sheet-column-mapping', methods=['GET'])
def get_sheet_column_mapping():
    """获取 Sheet 列映射配置"""
    try:
        mapping = config_service.get_sheet_column_mapping()
        return jsonify({"success": True, "data": mapping})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/sheet-column-mapping', methods=['PUT'])
def set_sheet_column_mapping():
    """设置 Sheet 列映射配置"""
    try:
        mapping = request.get_json()
        if not isinstance(mapping, dict):
            return jsonify({"success": False, "error": "配置格式错误"}), 400

        # 创建备份
        from ..services import BackupService
        BackupService().create_backup()

        config_service.set_sheet_column_mapping(mapping)
        return jsonify({"success": True, "message": "列映射配置保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/sheet-column-mapping/<path:sheet_name>', methods=['GET'])
def get_sheet_mapping(sheet_name: str):
    """获取单个 Sheet 的列映射配置"""
    try:
        sheet_config = config_service.get_sheet_mapping(sheet_name)
        if sheet_config:
            return jsonify({"success": True, "data": sheet_config})
        return jsonify({"success": False, "error": "Sheet 配置不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/sheet-column-mapping/<path:sheet_name>', methods=['PUT'])
def set_sheet_mapping(sheet_name: str):
    """设置单个 Sheet 的列映射配置"""
    try:
        sheet_config = request.get_json()
        if not sheet_config:
            return jsonify({"success": False, "error": "配置数据不能为空"}), 400

        # 创建备份
        from ..services import BackupService
        BackupService().create_backup()

        config_service.set_sheet_mapping(sheet_name, sheet_config)
        return jsonify({"success": True, "message": "Sheet 列映射保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/sheet-column-mapping/<path:sheet_name>', methods=['DELETE'])
def delete_sheet_mapping(sheet_name: str):
    """删除 Sheet 列映射"""
    try:
        if config_service.delete_sheet_mapping(sheet_name):
            return jsonify({"success": True, "message": "Sheet 列映射删除成功"})
        return jsonify({"success": False, "error": "Sheet 配置不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== 批量保存（Excel 一键保存） ==========

@config_bp.route('/batch-save', methods=['POST'])
def batch_save_sheets():
    """
    批量保存 Sheet 配置（用于 Excel 一键保存功能）

    请求体:
        {
            "sheets": [
                {"name": "Sheet1", "columns": [...], "is_first_sheet": true},
                {"name": "Sheet2", "columns": [...], "is_first_sheet": false}
            ]
        }

    响应:
        {
            "success": true,
            "message": "配置已保存",
            "updated": {
                "sheet_column_mapping": ["Sheet1", "Sheet2"],
                "priority_rules": ["Sheet2"]
            }
        }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请求数据不能为空"}), 400

        sheets = data.get('sheets', [])
        if not isinstance(sheets, list):
            return jsonify({"success": False, "error": "sheets 格式错误"}), 400

        if not sheets:
            return jsonify({"success": False, "error": "sheets 不能为空"}), 400

        # 创建备份
        from ..services import BackupService
        BackupService().create_backup()

        # 执行批量保存
        updated = config_service.batch_save_sheets(sheets)

        return jsonify({
            "success": True,
            "message": "配置已保存",
            "updated": updated
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
