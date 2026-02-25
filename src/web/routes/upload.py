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
# Excel 上传限制（10MB）
MAX_EXCEL_SIZE = 10 * 1024 * 1024


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
            "error": f"文件大小超过限制（最大 10MB）"
        }), 400

    try:
        # 使用 pandas 读取第一行表头
        import pandas as pd
        import tempfile

        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # 读取第一个 Sheet 的表头
        df = pd.read_excel(tmp_path, nrows=0)
        columns = df.columns.tolist()

        # 过滤掉 Unnamed 列
        columns = [col for col in columns if not str(col).startswith('Unnamed')]

        # 删除临时文件
        os.unlink(tmp_path)

        return jsonify({
            "success": True,
            "columns": columns,
            "count": len(columns)
        })

    except Exception as e:
        return jsonify({"success": False, "error": f"解析 Excel 失败: {str(e)}"}), 500
