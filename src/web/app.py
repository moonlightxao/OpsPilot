# -*- coding: utf-8 -*-
"""
Flask 应用工厂
创建和配置 Flask 应用实例
"""

from pathlib import Path
from flask import Flask, render_template


def create_app(config_path: str = "config/rules.yaml") -> Flask:
    """
    创建 Flask 应用实例

    Args:
        config_path: 配置文件路径

    Returns:
        Flask 应用实例
    """
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static',
        static_url_path='/static'
    )

    # 配置
    app.config['SECRET_KEY'] = 'opspilot-web-config-secret'
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
    app.config['CONFIG_PATH'] = config_path

    # 注册蓝图
    from .routes import config_bp, backup_bp, upload_bp
    app.register_blueprint(config_bp)
    app.register_blueprint(backup_bp)
    app.register_blueprint(upload_bp)

    # 图片静态文件服务
    from flask import send_from_directory
    @app.route('/images/<filename>')
    def serve_image(filename):
        """提供上传图片的访问"""
        return send_from_directory(Path('config/images'), filename)

    # 主页面路由
    @app.route('/')
    def index():
        """配置中心主页面"""
        return render_template('index.html')

    @app.route('/chapters')
    def chapters():
        """章节排序配置页面"""
        return render_template('index.html', active_tab='chapters')

    @app.route('/actions')
    def actions():
        """操作类型配置页面"""
        return render_template('index.html', active_tab='actions')

    @app.route('/columns')
    def columns():
        """列映射配置页面"""
        return render_template('index.html', active_tab='columns')

    @app.route('/backups')
    def backups():
        """版本回滚页面"""
        return render_template('index.html', active_tab='backups')

    # 错误处理
    @app.errorhandler(404)
    def not_found(e):
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return {"success": False, "error": "服务器内部错误"}, 500

    return app
