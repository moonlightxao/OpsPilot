# -*- coding: utf-8 -*-
"""
备份服务 - 配置版本管理
负责创建备份、清理旧备份、版本回滚
"""

import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any


class BackupService:
    """配置备份管理服务"""

    MAX_BACKUPS = 10  # 最多保留 10 个备份
    BACKUP_PREFIX = "rules.yaml.bak."

    def __init__(self, config_path: str = "config/rules.yaml", backup_dir: str = "config/backups"):
        """
        初始化备份服务

        Args:
            config_path: 配置文件路径
            backup_dir: 备份目录
        """
        self.config_path = Path(config_path)
        self.backup_dir = Path(backup_dir)

    def create_backup(self) -> Optional[str]:
        """
        创建配置备份

        Returns:
            备份文件名（不含路径），失败返回 None
        """
        if not self.config_path.exists():
            return None

        # 确保备份目录存在
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.BACKUP_PREFIX}{timestamp}"
        backup_path = self.backup_dir / backup_filename

        # 复制文件
        shutil.copy2(self.config_path, backup_path)

        # 清理旧备份
        self._cleanup_old_backups()

        return backup_filename

    def _cleanup_old_backups(self) -> None:
        """清理旧备份，保留最近 MAX_BACKUPS 个"""
        backups = sorted(
            self.backup_dir.glob(f"{self.BACKUP_PREFIX}*"),
            key=lambda p: p.name
        )

        # 删除超出数量的旧备份
        for old_backup in backups[:-self.MAX_BACKUPS]:
            old_backup.unlink()

    def list_backups(self) -> List[Dict[str, Any]]:
        """
        获取备份列表

        Returns:
            备份信息列表，按时间倒序
        """
        if not self.backup_dir.exists():
            return []

        backups = []
        for backup_path in self.backup_dir.glob(f"{self.BACKUP_PREFIX}*"):
            # 解析时间戳
            timestamp_str = backup_path.name.replace(self.BACKUP_PREFIX, "")
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            except ValueError:
                continue

            backups.append({
                "filename": backup_path.name,
                "timestamp": timestamp_str,
                "datetime": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "size": backup_path.stat().st_size,
            })

        # 按时间倒序
        backups.sort(key=lambda x: x["timestamp"], reverse=True)
        return backups

    def get_backup_content(self, filename: str) -> Optional[str]:
        """
        获取备份文件内容

        Args:
            filename: 备份文件名

        Returns:
            备份内容，失败返回 None
        """
        backup_path = self.backup_dir / filename

        # 安全检查：防止路径遍历攻击
        if not backup_path.resolve().is_relative_to(self.backup_dir.resolve()):
            return None

        if not backup_path.exists():
            return None

        with open(backup_path, 'r', encoding='utf-8') as f:
            return f.read()

    def restore_backup(self, filename: str) -> bool:
        """
        回滚到指定版本

        Args:
            filename: 备份文件名

        Returns:
            是否回滚成功
        """
        backup_path = self.backup_dir / filename

        # 安全检查：防止路径遍历攻击
        if not backup_path.resolve().is_relative_to(self.backup_dir.resolve()):
            return False

        if not backup_path.exists():
            return False

        # 在回滚前，先备份当前配置
        self.create_backup()

        # 执行回滚
        shutil.copy2(backup_path, self.config_path)
        return True

    def delete_backup(self, filename: str) -> bool:
        """
        删除指定备份

        Args:
            filename: 备份文件名

        Returns:
            是否删除成功
        """
        backup_path = self.backup_dir / filename

        # 安全检查
        if not backup_path.resolve().is_relative_to(self.backup_dir.resolve()):
            return False

        if backup_path.exists():
            backup_path.unlink()
            return True
        return False
