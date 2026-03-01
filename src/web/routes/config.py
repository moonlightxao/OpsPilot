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

        from ..services import BackupService
        BackupService().create_backup()

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


@config_bp.route('/priority-rules/batch-delete', methods=['POST'])
def batch_delete_chapters():
    """批量删除章节"""
    try:
        data = request.get_json()
        sheet_names = data.get('sheet_names', [])

        if not isinstance(sheet_names, list):
            return jsonify({"success": False, "error": "参数格式错误"}), 400

        if not sheet_names:
            return jsonify({"success": False, "error": "请选择要删除的章节"}), 400

        from ..services import BackupService
        BackupService().create_backup()

        deleted = config_service.batch_delete_chapters(sheet_names)

        return jsonify({
            "success": True,
            "message": f"已删除 {len(deleted)} 个章节",
            "deleted": deleted
        })
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

        from ..services import BackupService
        BackupService().create_backup()

        config_service.set_action_library(library)
        return jsonify({"success": True, "message": "操作类型配置保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/action-library/batch-delete', methods=['POST'])
def batch_delete_actions():
    """批量删除操作类型"""
    try:
        data = request.get_json()
        chapter = data.get('chapter')
        action_names = data.get('action_names', [])

        if not chapter:
            return jsonify({"success": False, "error": "缺少章节参数"}), 400

        if not isinstance(action_names, list):
            return jsonify({"success": False, "error": "参数格式错误"}), 400

        if not action_names:
            return jsonify({"success": False, "error": "请选择要删除的操作类型"}), 400

        from ..services import BackupService
        BackupService().create_backup()

        deleted = config_service.batch_delete_chapter_actions(chapter, action_names)

        return jsonify({
            "success": True,
            "message": f"已删除 {len(deleted)} 个操作类型",
            "deleted": deleted
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== 章节操作类型配置（v2 新增） ==========
# 注意：这些路由必须放在 /action-library/<action_name> 路由之前
# 因为 Flask 按定义顺序匹配路由

@config_bp.route('/action-library/chapter/<path:chapter>', methods=['GET'])
def get_chapter_actions(chapter: str):
    """获取指定章节的操作类型列表"""
    try:
        actions = config_service.get_chapter_actions(chapter)
        return jsonify({"success": True, "data": actions})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/action-library/chapter/<path:chapter>', methods=['PUT'])
def set_chapter_actions(chapter: str):
    """设置指定章节的操作类型配置"""
    try:
        actions = request.get_json()
        if not isinstance(actions, dict):
            return jsonify({"success": False, "error": "配置格式错误"}), 400

        from ..services import BackupService
        BackupService().create_backup()

        config_service.set_chapter_actions(chapter, actions)
        return jsonify({"success": True, "message": "章节操作类型配置保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/action-library/chapter/<path:chapter>/<path:action_name>', methods=['PUT'])
def set_chapter_action(chapter: str, action_name: str):
    """设置指定章节的某个操作类型"""
    try:
        action_config = request.get_json()
        if not action_config:
            return jsonify({"success": False, "error": "配置数据不能为空"}), 400

        from ..services import BackupService
        BackupService().create_backup()

        config_service.set_chapter_action(chapter, action_name, action_config)
        return jsonify({"success": True, "message": "操作类型保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/action-library/chapter/<path:chapter>/<path:action_name>', methods=['DELETE'])
def delete_chapter_action(chapter: str, action_name: str):
    """删除指定章节的某个操作类型"""
    try:
        if config_service.delete_chapter_action(chapter, action_name):
            return jsonify({"success": True, "message": "操作类型删除成功"})
        return jsonify({"success": False, "error": "操作类型不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== 兼容旧 API（放在章节路由之后） ==========

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

        from ..services import BackupService
        BackupService().create_backup()

        config_service.set_sheet_column_mapping(mapping)
        return jsonify({"success": True, "message": "列映射配置保存成功"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@config_bp.route('/sheet-column-mapping/batch-delete', methods=['POST'])
def batch_delete_mappings():
    """批量删除 Sheet 列映射"""
    try:
        data = request.get_json()
        sheet_names = data.get('sheet_names', [])

        if not isinstance(sheet_names, list):
            return jsonify({"success": False, "error": "参数格式错误"}), 400

        if not sheet_names:
            return jsonify({"success": False, "error": "请选择要删除的 Sheet"}), 400

        from ..services import BackupService
        BackupService().create_backup()

        deleted = config_service.batch_delete_sheet_mappings(sheet_names)

        return jsonify({
            "success": True,
            "message": f"已删除 {len(deleted)} 个 Sheet 列映射",
            "deleted": deleted
        })
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
    批量保存 Sheet 配置（V5 全量覆盖模式）

    V5 更新：
    - 全量覆盖 sheet_column_mapping 和 priority_rules
    - 全量重新生成 core_fields
    - 返回 updated 和 deleted 信息
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

        from ..services import BackupService
        BackupService().create_backup()

        result = config_service.batch_save_sheets(sheets)

        # 构建响应消息
        message_parts = ["配置已保存"]
        if result.get("deleted", {}).get("sheet_column_mapping"):
            message_parts.append(f"已清理 {len(result['deleted']['sheet_column_mapping'])} 个废弃 Sheet 配置")
        if result.get("deleted", {}).get("core_fields"):
            message_parts.append(f"已清理 {len(result['deleted']['core_fields'])} 个废弃核心字段")

        return jsonify({
            "success": True,
            "message": "，".join(message_parts),
            "updated": result.get("updated", {}),
            "deleted": result.get("deleted", {})
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========== 核心字段同步 ==========

@config_bp.route('/sync-core-fields', methods=['POST'])
def sync_core_fields():
    """
    同步核心字段

    从 sheet_column_mapping 中收集所有列名，
    根据关键词匹配规则更新 core_fields 的 aliases
    """
    try:
        from ..services import BackupService
        BackupService().create_backup()

        result = config_service.sync_core_fields_from_columns()

        if result["synced_count"] > 0:
            return jsonify({
                "success": True,
                "message": f"已同步 {result['synced_count']} 个核心字段",
                "data": result
            })
        else:
            return jsonify({
                "success": True,
                "message": "无需同步，所有列名已存在于核心字段中",
                "data": result
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== 批量保存操作类型（V6 新增） ==========

@config_bp.route('/batch-save-action-types', methods=['POST'])
def batch_save_action_types():
    """
    批量保存操作类型（V6 新增）

    接收用户确认的操作类型列表，保存到 action_library

    请求体:
    {
        "action_types": {
            "Sheet名": {
                "操作类型名": {"overwrite": true/false}
            }
        }
    }

    返回:
    {
        "success": true,
        "message": "已保存 N 个操作类型",
        "result": {
            "added": {"Sheet名": ["新增1", "新增2"]},
            "updated": {"Sheet名": ["覆盖1"]},
            "skipped": {"Sheet名": ["跳过1"]}
        }
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "请求数据不能为空"}), 400

        action_types = data.get('action_types', {})
        if not isinstance(action_types, dict):
            return jsonify({"success": False, "error": "action_types 格式错误"}), 400

        if not action_types:
            return jsonify({"success": False, "error": "action_types 不能为空"}), 400

        from ..services import BackupService
        BackupService().create_backup()

        result = config_service.batch_save_action_types(action_types)

        # 构建响应消息
        total_count = (
            sum(len(v) for v in result.get("added", {}).values()) +
            sum(len(v) for v in result.get("updated", {}).values())
        )
        skipped_count = sum(len(v) for v in result.get("skipped", {}).values())

        message_parts = [f"已保存 {total_count} 个操作类型"]
        if skipped_count > 0:
            message_parts.append(f"跳过 {skipped_count} 个已存在的操作类型")

        return jsonify({
            "success": True,
            "message": "，".join(message_parts),
            "result": result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
