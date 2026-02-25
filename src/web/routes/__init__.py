# -*- coding: utf-8 -*-
"""Web 路由模块"""
from .config import config_bp
from .backup import backup_bp
from .upload import upload_bp

__all__ = ['config_bp', 'backup_bp', 'upload_bp']
