# -*- coding: utf-8 -*-
"""
上传路由 - 图片上传 API
"""

import os
import uuid
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import Blueprint, jsonify, request, current_app

upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')

# 允许的图片类型
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# 图片大小限制（5MB）
MAX_IMAGE_SIZE = 5 * 1024 * 1024
# Excel 上传限制（50MB）
MAX_EXCEL_SIZE = 50 * 1024 * 1024


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@upload_bp.route('/image', methods=['POST'])
def upload_image():
    """
    上传图片

    Returns:
        JSON: {"success": true, "url": "/images/xxx.png"}
    """
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "未选择文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "未选择文件"}), 400

    if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
        return jsonify({
            "success": False,
            "error": f"不支持的文件类型，仅支持: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        }), 400

    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_IMAGE_SIZE:
        return jsonify({
            "success": False,
            "error": f"文件大小超过限制（最大 5MB）"
        }), 400

    # 生成安全的文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{timestamp}_{unique_id}.{ext}"

    # 确保目录存在
    upload_dir = Path('config/images')
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 保存文件
    filepath = upload_dir / filename
    file.save(filepath)

    # 返回相对 URL（用于 TinyMCE）
    return jsonify({
        "success": True,
        "url": f"/images/{filename}",
        "filename": filename
    })


@upload_bp.route('/excel', methods=['POST'])
def upload_excel():
    """
    上传 Excel 文件用于列名识别

    Returns:
        JSON: {"success": true, "columns": ["列1", "列2", ...]}
    """
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "未选择文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "未选择文件"}), 400

    # 检查文件扩展名
    allowed_excel = {'xlsx', 'xls'}
    if not allowed_file(file.filename, allowed_excel):
        return jsonify({
            "success": False,
            "error": f"不支持的文件类型，仅支持: {', '.join(allowed_excel)}"
        }), 400

    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_EXCEL_SIZE:
        return jsonify({
            "success": False,
            "error": f"文件大小超过限制（最大 50MB）"
        }), 400

    tmp_path = None
    try:
        import pandas as pd
        import tempfile

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # 读取所有 Sheet 的表头
        all_sheets = {}
        sheet_names = []

        with pd.ExcelFile(tmp_path) as xl:
            sheet_names = xl.sheet_names
            for sheet_name in sheet_names:
                df = pd.read_excel(xl, sheet_name=sheet_name, nrows=0)
                columns = df.columns.tolist()
                # 过滤掉 Unnamed 列
                columns = [col for col in columns if not str(col).startswith('Unnamed')]
                all_sheets[sheet_name] = columns

        return jsonify({
            "success": True,
            "sheets": all_sheets,
            "sheet_names": list(all_sheets.keys()),
            "columns": all_sheets.get(sheet_names[0], []),
            "count": sum(len(cols) for cols in all_sheets.values())
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"解析 Excel 失败: {str(e)}"}), 500
    finally:
        # 确保临时文件被删除
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass


@upload_bp.route('/excel/preview', methods=['POST'])
def upload_excel_preview():
    """
    Excel 一键保存预览接口（V6 增强）

    上传 Excel 文件，返回所有 Sheet 及列名预览，用于"一键保存"功能
    V6 新增：自动识别每个 Sheet 的操作类型列，返回识别到的操作类型列表

    Returns:
        JSON: {
            "success": true,
            "sheets": [{"name": "Sheet1", "columns": [...], "is_first_sheet": true}],
            "current_priority_rules": ["Sheet2", "Sheet3"],
            "max_priority": 20,
            "recognized_action_types": {
                "Sheet1": {"column_name": "操作类型", "action_types": ["新增", "删除"]}
            },
            "existing_action_types": {
                "Sheet1": ["新增"]
            }
        }
    """
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "未选择文件"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "未选择文件"}), 400

    # 检查文件扩展名
    allowed_excel = {'xlsx', 'xls'}
    if not allowed_file(file.filename, allowed_excel):
        return jsonify({
            "success": False,
            "error": f"不支持的文件类型，仅支持: {', '.join(allowed_excel)}"
        }), 400

    # 检查文件大小
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_EXCEL_SIZE:
        return jsonify({
            "success": False,
            "error": "文件大小超过限制（最大 50MB）"
        }), 400

    tmp_path = None
    try:
        import pandas as pd
        import tempfile
        from ..services import ConfigService

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # 获取配置
        config_service = ConfigService()
        core_fields = config_service.load().get("core_fields", {})
        action_type_aliases = core_fields.get("action_type", {}).get("aliases", ["操作类型", "操作", "action"])

        # 获取已存在的操作类型
        action_library = config_service.get_action_library()
        existing_action_types = {}
        for chapter, actions in action_library.items():
            existing_action_types[chapter] = list(actions.keys()) if actions else []

        # 读取所有 Sheet 并识别操作类型
        sheets = []
        recognized_action_types = {}

        with pd.ExcelFile(tmp_path) as xl:
            sheet_names = xl.sheet_names
            for idx, sheet_name in enumerate(sheet_names):
                # 读取表头
                df_header = pd.read_excel(xl, sheet_name=sheet_name, nrows=0)
                columns = df_header.columns.tolist()
                # 过滤掉 Unnamed 列
                columns = [col for col in columns if not str(col).startswith('Unnamed')]

                sheets.append({
                    "name": sheet_name,
                    "columns": columns,
                    "is_first_sheet": (idx == 0)
                })

                # 识别操作类型列
                action_type_column = _find_action_type_column(columns, action_type_aliases)

                if action_type_column:
                    # 读取数据行（最多1000行用于识别）
                    df_data = pd.read_excel(xl, sheet_name=sheet_name, usecols=[action_type_column])
                    # 提取去重的操作类型值
                    action_values = df_data[action_type_column].dropna().astype(str).str.strip().unique().tolist()
                    # 过滤空字符串
                    action_values = [v for v in action_values if v]

                    if action_values:
                        recognized_action_types[sheet_name] = {
                            "column_name": action_type_column,
                            "action_types": action_values
                        }

        # 获取当前配置信息
        priority_rules = config_service.get_priority_rules()

        # 获取已存在的章节名称列表
        current_priority_rules = list(priority_rules.keys()) if isinstance(priority_rules, dict) else []

        # 获取当前最大优先级
        if isinstance(priority_rules, dict) and priority_rules:
            max_priority = max(priority_rules.values())
        else:
            max_priority = 0

        return jsonify({
            "success": True,
            "sheets": sheets,
            "current_priority_rules": current_priority_rules,
            "max_priority": max_priority,
            "recognized_action_types": recognized_action_types,
            "existing_action_types": existing_action_types
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"解析 Excel 失败: {str(e)}"}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except:
                pass


def _find_action_type_column(columns: list, aliases: list) -> str:
    """
    在列名列表中查找操作类型列

    Args:
        columns: 列名列表
        aliases: 操作类型列的别名列表

    Returns:
        匹配的列名，无匹配返回 None
    """
    for col in columns:
        col_str = str(col).lower().strip()
        for alias in aliases:
            if alias.lower() in col_str:
                return str(col)
    return None
