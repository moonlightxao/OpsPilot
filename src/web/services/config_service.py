# -*- coding: utf-8 -*-
"""
配置服务 - YAML 读写服务
负责 rules.yaml 的读取、解析、修改和保存
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class ConfigService:
    """YAML 配置读写服务"""

    def __init__(self, config_path: str = "config/rules.yaml"):
        """
        初始化配置服务

        Args:
            config_path: 配置文件路径，默认为 config/rules.yaml
        """
        self.config_path = Path(config_path)
        self._config_cache: Optional[Dict[str, Any]] = None

    def load(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载配置文件

        Args:
            force_reload: 是否强制重新加载（忽略缓存）

        Returns:
            配置字典
        """
        if self._config_cache is not None and not force_reload:
            return self._config_cache

        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config_cache = yaml.safe_load(f) or {}

        return self._config_cache

    def save(self, config: Dict[str, Any]) -> None:
        """
        保存配置到文件

        Args:
            config: 配置字典
        """
        # 确保目录存在
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存前验证 YAML 语法
        try:
            yaml.safe_dump(config, allow_unicode=True)
        except yaml.YAMLError as e:
            raise ValueError(f"配置格式错误: {e}")

        with open(self.config_path, 'w', encoding='utf-8') as f:
            # 添加文件头注释
            f.write("# ============================================================\n")
            f.write("# OpsPilot 规则配置文件\n")
            f.write(f"# 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("# ============================================================\n\n")
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        # 更新缓存
        self._config_cache = config

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取指定配置项

        Args:
            key: 配置键（支持点号分隔的嵌套访问）
            default: 默认值

        Returns:
            配置值
        """
        config = self.load()
        keys = key.split('.')
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        设置指定配置项

        Args:
            key: 配置键（支持点号分隔的嵌套设置）
            value: 配置值
        """
        config = self.load()
        keys = key.split('.')

        # 嵌套设置
        current = config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        self.save(config)

    # ========== 章节排序相关 ==========

    def get_priority_rules(self) -> Dict[str, int]:
        """获取章节优先级配置"""
        return self.get('priority_rules', {})

    def set_priority_rules(self, priority_rules: Dict[str, int]) -> None:
        """设置章节优先级配置"""
        config = self.load()
        config['priority_rules'] = priority_rules
        self.save(config)

    def add_chapter(self, sheet_name: str, priority: int) -> None:
        """
        添加新章节

        Args:
            sheet_name: Sheet 名称
            priority: 优先级数值
        """
        priority_rules = self.get_priority_rules()
        priority_rules[sheet_name] = priority
        self.set_priority_rules(priority_rules)

    def delete_chapter(self, sheet_name: str) -> bool:
        """
        删除章节

        Args:
            sheet_name: Sheet 名称

        Returns:
            是否删除成功
        """
        priority_rules = self.get_priority_rules()
        if sheet_name in priority_rules:
            del priority_rules[sheet_name]
            self.set_priority_rules(priority_rules)
            return True
        return False

    # ========== 操作类型相关 ==========

    def get_action_library(self) -> Dict[str, Dict[str, Any]]:
        """获取操作类型配置"""
        return self.get('action_library', {})

    def set_action_library(self, action_library: Dict[str, Dict[str, Any]]) -> None:
        """设置操作类型配置"""
        config = self.load()
        config['action_library'] = action_library
        # 同步高危关键字列表
        self._sync_high_risk_keywords(config, action_library)
        self.save(config)

    def get_action(self, action_name: str) -> Optional[Dict[str, Any]]:
        """获取单个操作类型配置"""
        action_library = self.get_action_library()
        return action_library.get(action_name)

    def set_action(self, action_name: str, action_config: Dict[str, Any]) -> None:
        """设置单个操作类型配置"""
        action_library = self.get_action_library()
        action_library[action_name] = action_config
        self.set_action_library(action_library)

    def delete_action(self, action_name: str) -> bool:
        """删除操作类型"""
        action_library = self.get_action_library()
        if action_name in action_library:
            del action_library[action_name]
            self.set_action_library(action_library)
            return True
        return False

    def _sync_high_risk_keywords(self, config: Dict[str, Any], action_library: Dict[str, Dict[str, Any]]) -> None:
        """同步高危关键字列表（自动从 action_library 中提取）"""
        high_risk_keywords = [
            name for name, cfg in action_library.items()
            if cfg.get('is_high_risk', False)
        ]
        config['high_risk_keywords'] = high_risk_keywords

    # ========== 列映射相关 ==========

    def get_sheet_column_mapping(self) -> Dict[str, Dict[str, Any]]:
        """获取 Sheet 列映射配置"""
        return self.get('sheet_column_mapping', {})

    def set_sheet_column_mapping(self, mapping: Dict[str, Dict[str, Any]]) -> None:
        """设置 Sheet 列映射配置"""
        config = self.load()
        config['sheet_column_mapping'] = mapping
        self.save(config)

    def get_sheet_mapping(self, sheet_name: str) -> Optional[Dict[str, Any]]:
        """获取单个 Sheet 的列映射配置"""
        mapping = self.get_sheet_column_mapping()
        return mapping.get(sheet_name)

    def set_sheet_mapping(self, sheet_name: str, sheet_config: Dict[str, Any]) -> None:
        """设置单个 Sheet 的列映射配置"""
        mapping = self.get_sheet_column_mapping()
        mapping[sheet_name] = sheet_config
        self.set_sheet_column_mapping(mapping)

    def delete_sheet_mapping(self, sheet_name: str) -> bool:
        """删除 Sheet 列映射"""
        mapping = self.get_sheet_column_mapping()
        if sheet_name in mapping:
            del mapping[sheet_name]
            self.set_sheet_column_mapping(mapping)
            return True
        return False

    # ========== 实施总表配置相关 ==========

    def get_implementation_summary_config(self) -> Dict[str, Any]:
        """获取实施总表配置"""
        return self.get('implementation_summary', {})

    def set_implementation_summary_config(self, config: Dict[str, Any]) -> None:
        """设置实施总表配置"""
        full_config = self.load()
        full_config['implementation_summary'] = config
        self.save(full_config)

    # ========== 批量保存相关 ==========

    def batch_save_sheets(self, sheets: list) -> dict:
        """
        批量保存 Sheet 配置（用于 Excel 一键保存功能）

        规则：
        1. 第一个 Sheet (上线安排) 跳过章节排序，仅保存列映射
        2. 其他 Sheet：
           - 列映射：始终更新 sheet_column_mapping
           - 章节排序：仅当 Sheet 名称不存在时才新增
        3. 新增章节的优先级 = 当前最大优先级 + 10

        Args:
            sheets: Sheet 列表，每个元素包含 name, columns, is_first_sheet

        Returns:
            更新结果 {"sheet_column_mapping": [...], "priority_rules": [...]}
        """
        config = self.load()
        updated = {"sheet_column_mapping": [], "priority_rules": []}

        # 确保 sheet_column_mapping 存在
        if "sheet_column_mapping" not in config:
            config["sheet_column_mapping"] = {}

        # 确保 priority_rules 存在且为 dict
        if "priority_rules" not in config:
            config["priority_rules"] = {}

        # 获取当前最大优先级
        priority_rules = config.get("priority_rules", {})
        if isinstance(priority_rules, dict) and priority_rules:
            max_priority = max(priority_rules.values())
        else:
            max_priority = 0
            # 如果 priority_rules 不是 dict，重置为 dict
            if not isinstance(priority_rules, dict):
                config["priority_rules"] = {}
                priority_rules = {}

        for sheet in sheets:
            name = sheet.get("name")
            columns = sheet.get("columns", [])
            is_first = sheet.get("is_first_sheet", False)

            if not name:
                continue

            # 1. 更新列映射（列名同时作为标准列名和别名）
            column_mapping = {col: [col] for col in columns}
            config["sheet_column_mapping"][name] = {
                "columns": columns,
                "column_mapping": column_mapping
            }
            updated["sheet_column_mapping"].append(name)

            # 2. 更新章节排序（仅非第一个 Sheet 且不存在时）
            if not is_first:
                if name not in priority_rules:
                    max_priority += 10
                    config["priority_rules"][name] = max_priority
                    priority_rules[name] = max_priority
                    updated["priority_rules"].append(name)

        self.save(config)
        return updated
