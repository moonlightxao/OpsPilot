# -*- coding: utf-8 -*-
"""
备份路由 - 备份管理 API
"""

from flask import Blueprint, jsonify, request
from ..services import BackupService

backup_bp = Blueprint('backup', __name__, url_prefix='/api/backups')
backup_service = BackupService()


@backup_bp.route('', methods=['GET'])
def list_backups():
    """获取备份列表（最近 10 条）"""
    try:
        backups = backup_service.list_backups()
        return jsonify({"success": True, "data": backups})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@backup_bp.route('/create', methods=['POST'])
def create_backup():
    """手动创建备份"""
    try:
        filename = backup_service.create_backup()
        if filename:
            return jsonify({"success": True, "message": "备份创建成功", "filename": filename})
        return jsonify({"success": False, "error": "配置文件不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@backup_bp.route('/<filename>', methods=['GET'])
def get_backup_content(filename: str):
    """获取指定备份内容"""
    try:
        content = backup_service.get_backup_content(filename)
        if content:
            return jsonify({"success": True, "data": content})
        return jsonify({"success": False, "error": "备份文件不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@backup_bp.route('/<filename>/restore', methods=['POST'])
def restore_backup(filename: str):
    """回滚到指定版本"""
    try:
        # 检查是否需要二次确认
        data = request.get_json() or {}
        confirmed = data.get('confirmed', False)

        if not confirmed:
            return jsonify({
                "success": False,
                "error": "需要确认回滚操作",
                "requires_confirmation": True
            }), 400

        if backup_service.restore_backup(filename):
            return jsonify({"success": True, "message": "回滚成功"})
        return jsonify({"success": False, "error": "备份文件不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@backup_bp.route('/<filename>', methods=['DELETE'])
def delete_backup(filename: str):
    """删除指定备份"""
    try:
        if backup_service.delete_backup(filename):
            return jsonify({"success": True, "message": "备份删除成功"})
        return jsonify({"success": False, "error": "备份文件不存在"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
