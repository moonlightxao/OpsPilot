# -*- coding: utf-8 -*-
"""
配置服务 - YAML 读写服务
负责 rules.yaml 的读取、解析、修改和保存
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


# 核心字段关键词映射
CORE_FIELD_KEYWORDS = {
    "action_type": ["操作类型", "操作", "action"],
    "deploy_unit": ["部署单元", "应用名", "服务名", "应用名称"],
    "executor": ["执行人", "实施人", "负责人", "复核人"],
    "task_name": ["任务名", "任务名称", "任务", "task"],
    "external_link": ["外部链接", "链接", "url"]
}


def _stringify_keys(obj: Any) -> Any:
    """
    递归地将字典键转换为字符串，确保与 JSON 兼容

    Args:
        obj: 任意 Python 对象

    Returns:
        转换后的对象（所有字典键都是字符串）
    """
    if isinstance(obj, dict):
        return {str(k): _stringify_keys(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_stringify_keys(item) for item in obj]
    return obj


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
            raw_config = yaml.safe_load(f) or {}

        # 将所有字典键转换为字符串，确保与 JSON 兼容
        self._config_cache = _stringify_keys(raw_config)

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

    def _is_flat_action_library(self, library: Dict[str, Any]) -> bool:
        """
        检测 action_library 是否为旧格式（扁平结构）

        旧格式示例:
        {
            "新增": {"instruction": "...", "is_high_risk": false},
            "删除": {"instruction": "...", "is_high_risk": true}
        }

        新格式示例:
        {
            "应用配置": {
                "新增": {"instruction": "...", "is_high_risk": false},
                "删除": {"instruction": "...", "is_high_risk": true}
            },
            "容器配置": {
                "扩容": {"instruction": "...", "is_high_risk": false}
            }
        }
        """
        if not library:
            return False
        first_value = next(iter(library.values()), {})
        # 旧格式: 顶层键的值包含 instruction 或 is_high_risk
        if isinstance(first_value, dict):
            return 'instruction' in first_value or 'is_high_risk' in first_value
        return False

    def get_action_library(self, auto_migrate: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        获取操作类型配置，自动兼容新旧格式

        Args:
            auto_migrate: 是否自动迁移旧格式到新格式

        Returns:
            操作类型配置（新格式）
        """
        raw_library = self.get('action_library', {})

        # 检测并迁移旧格式
        if self._is_flat_action_library(raw_library):
            if auto_migrate:
                # 迁移到新格式，归入"默认"章节
                return {"默认": raw_library}
            return raw_library

        return raw_library

    def set_action_library(self, action_library: Dict[str, Dict[str, Any]]) -> None:
        """设置操作类型配置"""
        config = self.load()
        config['action_library'] = action_library
        # 同步高危关键字列表
        self._sync_high_risk_keywords(config, action_library)
        self.save(config)

    # ========== 章节操作类型相关（v2 新增） ==========

    def get_chapter_actions(self, chapter: str) -> Dict[str, Dict[str, Any]]:
        """获取指定章节的操作类型配置"""
        library = self.get_action_library()
        return library.get(chapter, {})

    def set_chapter_actions(self, chapter: str, actions: Dict[str, Any]) -> None:
        """设置指定章节的操作类型配置"""
        library = self.get_action_library(auto_migrate=False)
        library[chapter] = actions
        self.set_action_library(library)

    def set_chapter_action(self, chapter: str, action_name: str, config: Dict[str, Any]) -> None:
        """设置指定章节的某个操作类型"""
        library = self.get_action_library(auto_migrate=False)
        if chapter not in library:
            library[chapter] = {}
        library[chapter][action_name] = config
        self.set_action_library(library)

    def delete_chapter_action(self, chapter: str, action_name: str) -> bool:
        """删除指定章节的某个操作类型"""
        library = self.get_action_library(auto_migrate=False)
        if chapter in library and action_name in library[chapter]:
            del library[chapter][action_name]
            self.set_action_library(library)
            return True
        return False

    # ========== 兼容旧 API ==========

    def get_action(self, action_name: str) -> Optional[Dict[str, Any]]:
        """获取单个操作类型配置（兼容旧格式）"""
        action_library = self.get_action_library()
        # 遍历所有章节查找
        for chapter, actions in action_library.items():
            if action_name in actions:
                return actions[action_name]
        return None

    def set_action(self, action_name: str, action_config: Dict[str, Any]) -> None:
        """设置单个操作类型配置（默认章节）"""
        library = self.get_action_library(auto_migrate=False)
        # 使用第一个章节或"默认"章节
        if library:
            first_chapter = next(iter(library.keys()))
        else:
            first_chapter = "默认"
            library[first_chapter] = {}
        library[first_chapter][action_name] = action_config
        self.set_action_library(library)

    def delete_action(self, action_name: str) -> bool:
        """删除操作类型（遍历所有章节）"""
        library = self.get_action_library(auto_migrate=False)
        for chapter, actions in library.items():
            if action_name in actions:
                del actions[action_name]
                self.set_action_library(library)
                return True
        return False

    # ========== 批量删除相关（v2 新增） ==========

    def batch_delete_chapter_actions(self, chapter: str, action_names: list) -> list:
        """批量删除指定章节的操作类型"""
        library = self.get_action_library(auto_migrate=False)
        deleted = []
        if chapter in library:
            for name in action_names:
                if name in library[chapter]:
                    del library[chapter][name]
                    deleted.append(name)
            if deleted:
                self.set_action_library(library)
        return deleted

    def batch_delete_chapters(self, sheet_names: list) -> list:
        """批量删除章节"""
        priority_rules = self.get_priority_rules()
        deleted = []
        for name in sheet_names:
            if name in priority_rules:
                del priority_rules[name]
                deleted.append(name)
        if deleted:
            self.set_priority_rules(priority_rules)
        return deleted

    def batch_delete_sheet_mappings(self, sheet_names: list) -> list:
        """批量删除 Sheet 列映射"""
        mapping = self.get_sheet_column_mapping()
        deleted = []
        for name in sheet_names:
            if name in mapping:
                del mapping[name]
                deleted.append(name)
        if deleted:
            self.set_sheet_column_mapping(mapping)
        return deleted

    def _sync_high_risk_keywords(self, config: Dict[str, Any], action_library: Dict[str, Any]) -> None:
        """
        同步高危关键字列表（从所有章节中提取）

        新格式 action_library 结构:
        {
            "章节名": {
                "操作类型名": {"is_high_risk": true/false, ...}
            }
        }
        """
        high_risk_keywords = []

        # 遍历所有章节
        for chapter, actions in action_library.items():
            if not isinstance(actions, dict):
                continue
            # 遍历该章节的所有操作类型
            for action_name, action_config in actions.items():
                if isinstance(action_config, dict) and action_config.get('is_high_risk', False):
                    high_risk_keywords.append(action_name)

        # 去重
        config['high_risk_keywords'] = list(set(high_risk_keywords))

    # ========== 列映射相关 ==========

    def _normalize_mapping(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """
        规范化列映射配置，确保所有键和列名都是字符串类型
        解决 YAML 解析时将纯数字列名解析为 int 导致的 JSON 序列化问题
        """
        if not mapping:
            return mapping

        normalized = {}
        for sheet_name, sheet_config in mapping.items():
            # 确保 Sheet 名称是字符串
            sheet_name = str(sheet_name)

            normalized[sheet_name] = {
                "columns": [str(col) for col in sheet_config.get("columns", [])],
                "column_mapping": {
                    str(col): [str(alias) for alias in aliases]
                    for col, aliases in sheet_config.get("column_mapping", {}).items()
                }
            }
        return normalized

    def get_sheet_column_mapping(self) -> Dict[str, Dict[str, Any]]:
        """获取 Sheet 列映射配置"""
        mapping = self.get('sheet_column_mapping', {})
        return self._normalize_mapping(mapping)

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

        V5 更新：全量覆盖模式
        - sheet_column_mapping：基于 Excel 完全重新生成，删除不存在的 Sheet
        - priority_rules：基于 Excel 完全重新生成（跳过第一个 Sheet），删除不存在的章节
        - action_library：保持不变
        - 自动调用 sync_core_fields_from_columns 进行全量同步

        规则：
        1. 第一个 Sheet (上线安排) 跳过章节排序，仅保存列映射
        2. 其他 Sheet：按顺序分配优先级（10, 20, 30...）
        3. 全量覆盖：原有配置中不存在于 Excel 的 Sheet/章节将被删除

        Args:
            sheets: Sheet 列表，每个元素包含 name, columns, is_first_sheet

        Returns:
            更新结果 {
                "updated": {"sheet_column_mapping": [...], "priority_rules": [...]},
                "deleted": {"sheet_column_mapping": [...], "priority_rules": [...], "core_fields": [...]}
            }
        """
        config = self.load()

        # 记录原有配置（用于计算被删除的项）
        old_sheet_mapping = set(config.get("sheet_column_mapping", {}).keys())
        old_priority_rules = set(config.get("priority_rules", {}).keys())

        # 全量重新生成 sheet_column_mapping
        new_sheet_mapping = {}
        new_priority_rules = {}
        updated_sheets = []
        updated_priorities = []

        priority_counter = 0

        for sheet in sheets:
            name = sheet.get("name")
            columns = sheet.get("columns", [])
            is_first = sheet.get("is_first_sheet", False)

            if not name:
                continue

            # 1. 生成列映射（列名同时作为标准列名和别名）
            column_mapping = {str(col): [str(col)] for col in columns}
            new_sheet_mapping[name] = {
                "columns": [str(col) for col in columns],
                "column_mapping": column_mapping
            }
            updated_sheets.append(name)

            # 2. 生成章节排序（仅非第一个 Sheet）
            if not is_first:
                priority_counter += 10
                new_priority_rules[name] = priority_counter
                updated_priorities.append(name)

        # 计算被删除的项
        new_sheet_names = set(new_sheet_mapping.keys())
        new_priority_names = set(new_priority_rules.keys())
        deleted_sheets = list(old_sheet_mapping - new_sheet_names)
        deleted_priorities = list(old_priority_rules - new_priority_names)

        # 全量覆盖配置
        config["sheet_column_mapping"] = new_sheet_mapping
        config["priority_rules"] = new_priority_rules

        # 保存配置（在同步 core_fields 之前）
        self.save(config)

        # 全量同步 core_fields
        sync_result = self._sync_core_fields_full(config, new_sheet_mapping)

        return {
            "updated": {
                "sheet_column_mapping": updated_sheets,
                "priority_rules": updated_priorities
            },
            "deleted": {
                "sheet_column_mapping": deleted_sheets,
                "priority_rules": deleted_priorities,
                "core_fields": sync_result.get("deleted", [])
            }
        }

    # ========== 核心字段同步相关 ==========

    def _sync_core_fields_full(self, config: dict, sheet_column_mapping: dict) -> dict:
        """
        全量重新生成 core_fields（V5 新增）

        同步规则：
        1. 保留预置核心字段的 required 属性
        2. 完全基于当前列名重新生成 core_fields
        3. 删除不存在的自定义字段
        4. 预置字段的别名完全基于当前列名重新生成

        Args:
            config: 配置字典
            sheet_column_mapping: 新的 sheet_column_mapping

        Returns:
            同步结果 {"synced_count": int, "deleted": [...]}
        """
        # 1. 收集所有列名并去重
        all_columns = set()
        for sheet_name, sheet_config in sheet_column_mapping.items():
            columns = sheet_config.get("columns", [])
            all_columns.update(columns)

        # 2. 获取原有 core_fields 中的自定义字段（用于计算删除）
        old_core_fields = config.get("core_fields", {})
        old_custom_fields = set(
            name for name, field in old_core_fields.items()
            if field.get("custom", False)
        )

        # 3. 重新生成 core_fields
        new_core_fields = {}

        # 预置核心字段名列表
        predefined_fields = set(CORE_FIELD_KEYWORDS.keys())

        # 先初始化预置字段（保留 required 属性）
        for field_name in predefined_fields:
            default_config = self._get_default_core_fields().get(field_name, {})
            new_core_fields[field_name] = {
                "aliases": [],
                "required": default_config.get("required", False)
            }

        # 4. 根据列名填充 aliases
        for column in all_columns:
            # 跳过纯数字列名（如 Excel 日期序列号 46315）
            if isinstance(column, (int, float)):
                continue
            # 确保列名是字符串
            column_str = str(column) if not isinstance(column, str) else column
            if not column_str.strip():
                continue

            matched_field = self._match_core_field(column_str)

            if matched_field and matched_field in new_core_fields:
                # 情况1: 匹配到预置核心字段，添加别名
                new_core_fields[matched_field]["aliases"].append(column_str)
            elif column_str not in predefined_fields:
                # 情况2: 未匹配且不是预置字段，创建自定义核心字段
                new_core_fields[column_str] = {
                    "aliases": [column_str],
                    "required": False,
                    "custom": True
                }

        # 5. 计算被删除的自定义字段
        new_custom_fields = set(
            name for name, field in new_core_fields.items()
            if field.get("custom", False)
        )
        deleted_fields = list(old_custom_fields - new_custom_fields)

        # 6. 保存配置（使用统一的 save 方法）
        config["core_fields"] = new_core_fields
        self.save(config)

        return {
            "synced_count": len([f for f in new_core_fields.values() if f.get("aliases")]),
            "deleted": deleted_fields
        }

    def sync_core_fields_from_columns(self) -> dict:
        """
        从 sheet_column_mapping 同步列名到 core_fields

        V5 更新：全量重新生成模式
        - 保留预置核心字段的 required 属性
        - 完全基于当前列名重新生成 core_fields
        - 删除不存在的自定义字段

        Returns:
            同步结果 {
                "synced_count": 同步的核心字段数量,
                "updated_fields": 更新的字段列表,
                "new_aliases": {字段名: [新增别名列表]},
                "new_fields": [新创建的字段列表],
                "deleted": [被删除的字段列表]
            }
        """
        config = self.load()
        sheet_column_mapping = config.get("sheet_column_mapping", {})

        # 1. 收集所有列名并去重
        all_columns = set()
        for sheet_name, sheet_config in sheet_column_mapping.items():
            columns = sheet_config.get("columns", [])
            all_columns.update(columns)

        # 2. 获取原有 core_fields（用于计算变更）
        old_core_fields = config.get("core_fields", {})
        old_custom_fields = set(
            name for name, field in old_core_fields.items()
            if field.get("custom", False)
        )

        # 3. 重新生成 core_fields
        new_core_fields = {}

        # 预置核心字段名列表
        predefined_fields = set(CORE_FIELD_KEYWORDS.keys())

        # 先初始化预置字段（保留 required 属性）
        for field_name in predefined_fields:
            old_required = old_core_fields.get(field_name, {}).get("required", False)
            default_config = self._get_default_core_fields().get(field_name, {})
            new_core_fields[field_name] = {
                "aliases": [],
                "required": old_required if field_name in old_core_fields else default_config.get("required", False)
            }

        result = {
            "synced_count": 0,
            "updated_fields": [],
            "new_aliases": {},
            "new_fields": [],
            "deleted": []
        }

        # 4. 根据列名填充 aliases
        for column in all_columns:
            # 跳过纯数字列名（如 Excel 日期序列号 46315）
            if isinstance(column, (int, float)):
                continue
            # 确保列名是字符串
            column_str = str(column) if not isinstance(column, str) else column
            if not column_str.strip():
                continue

            matched_field = self._match_core_field(column_str)

            if matched_field and matched_field in new_core_fields:
                # 情况1: 匹配到预置核心字段，添加别名
                new_core_fields[matched_field]["aliases"].append(column_str)

                if matched_field not in result["new_aliases"]:
                    result["new_aliases"][matched_field] = []
                result["new_aliases"][matched_field].append(column_str)

                if matched_field not in result["updated_fields"]:
                    result["updated_fields"].append(matched_field)

            elif column_str not in predefined_fields:
                # 情况2: 未匹配且不是预置字段，创建自定义核心字段
                new_core_fields[column_str] = {
                    "aliases": [column_str],
                    "required": False,
                    "custom": True
                }
                result["new_fields"].append(column_str)

                if column_str not in result["updated_fields"]:
                    result["updated_fields"].append(column_str)

        # 5. 计算被删除的自定义字段
        new_custom_fields = set(
            name for name, field in new_core_fields.items()
            if field.get("custom", False)
        )
        result["deleted"] = list(old_custom_fields - new_custom_fields)

        # 6. 保存配置
        config["core_fields"] = new_core_fields
        self.save(config)
        result["synced_count"] = len([f for f in new_core_fields.values() if f.get("aliases")])

        return result

    def _match_core_field(self, column_name: str) -> Optional[str]:
        """
        根据列名匹配核心字段

        Args:
            column_name: 列名

        Returns:
            匹配的核心字段名，无匹配返回 None
        """
        column_lower = column_name.lower()

        for field_name, keywords in CORE_FIELD_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in column_lower:
                    return field_name

        return None

    def _get_default_core_fields(self) -> dict:
        """获取默认的核心字段配置（所有字段均为非必填）"""
        return {
            "action_type": {
                "aliases": ["操作类型", "操作", "Action"],
                "required": False
            },
            "deploy_unit": {
                "aliases": ["部署单元", "应用名", "服务名"],
                "required": False
            },
            "executor": {
                "aliases": ["执行人", "实施人", "负责人"],
                "required": False
            },
            "external_link": {
                "aliases": ["外部链接", "链接", "URL"],
                "required": False
            },
            "task_name": {
                "aliases": ["任务名", "任务名称", "任务"],
                "required": False
            }
        }

    # ========== 操作类型自动识别相关（V6 新增） ==========

    def batch_save_action_types(self, action_types: dict) -> dict:
        """
        批量保存操作类型（V6 新增）

        将从 Excel 识别到的操作类型保存到 action_library

        Args:
            action_types: {
                "Sheet名": {
                    "操作类型名": {"overwrite": true/false},
                    ...
                },
                ...
            }

        Returns:
            {
                "added": {"Sheet名": ["新增的操作类型"]},
                "updated": {"Sheet名": ["覆盖的操作类型"]},
                "skipped": {"Sheet名": ["跳过的操作类型"]}
            }
        """
        config = self.load()
        action_library = config.get("action_library", {})

        result = {
            "added": {},
            "updated": {},
            "skipped": {}
        }

        for chapter, actions in action_types.items():
            if chapter not in action_library:
                action_library[chapter] = {}

            for action_name, options in actions.items():
                overwrite = options.get("overwrite", False)
                is_existing = action_name in action_library[chapter]

                if is_existing and not overwrite:
                    # 跳过已存在且不覆盖的
                    if chapter not in result["skipped"]:
                        result["skipped"][chapter] = []
                    result["skipped"][chapter].append(action_name)
                else:
                    # 新增或覆盖 - 生成默认模板
                    default_instruction = self._generate_default_instruction(action_name)
                    action_library[chapter][action_name] = {
                        "instruction": default_instruction,
                        "is_high_risk": False,
                        "render_table": True
                    }

                    if is_existing:
                        if chapter not in result["updated"]:
                            result["updated"][chapter] = []
                        result["updated"][chapter].append(action_name)
                    else:
                        if chapter not in result["added"]:
                            result["added"][chapter] = []
                        result["added"][chapter].append(action_name)

        config["action_library"] = action_library
        self.save(config)

        return result

    def _generate_default_instruction(self, action_name: str) -> str:
        """
        生成操作类型的默认步骤模板

        Args:
            action_name: 操作类型名称

        Returns:
            默认步骤模板文本
        """
        template = f"""【{action_name}操作说明】

1. 操作目的：
   - 请在此填写{action_name}操作的目的和预期效果

2. 前置条件：
   - 请确认操作所需的前置条件（如权限、环境等）

3. 操作步骤：
   - 步骤1：请在此填写具体操作步骤
   - 步骤2：请在此填写具体操作步骤
   - 步骤3：请在此填写具体操作步骤

4. 验证方法：
   - 请在此填写如何验证操作是否成功

5. 回滚方案：
   - 如操作失败，请在此填写回滚方法"""
        return template
