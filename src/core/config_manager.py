"""
统一配置管理器

提供单例模式的配置访问接口，从 config/rules.yaml 读取业务规则。
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


class ConfigManager:
    """统一配置管理器（单例）"""

    _instance: Optional['ConfigManager'] = None

    def __new__(cls, config_path: str = "config/rules.yaml"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_path: str = "config/rules.yaml"):
        if self._initialized:
            return

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load()
        self._initialized = True

    def _load(self) -> None:
        """加载配置"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}

    def reload(self) -> None:
        """重新加载配置"""
        self._load()

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项（支持点号分隔）"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @property
    def core_fields(self) -> Dict[str, Any]:
        return self._config.get('core_fields', {})

    @property
    def priority_rules(self) -> Dict[str, int]:
        return self._config.get('priority_rules', {})

    @property
    def action_library(self) -> Dict[str, Any]:
        return self._config.get('action_library', {})

    @property
    def high_risk_keywords(self) -> list:
        return self._config.get('high_risk_keywords', [])

    @property
    def implementation_summary(self) -> Dict[str, Any]:
        """获取实施总表配置"""
        return self._config.get('implementation_summary', {})

    @property
    def summary_extraction(self) -> Dict[str, Any]:
        """获取摘要提取配置"""
        return self._config.get('summary_extraction', {})

    @property
    def sheet_column_mapping(self) -> Dict[str, Any]:
        """获取 Sheet 列映射配置"""
        return self._config.get('sheet_column_mapping', {})

    def get_action_config(self, section_name: str, action_type: str) -> Optional[Dict[str, Any]]:
        """获取指定章节和操作类型的配置"""
        section_actions = self.action_library.get(section_name, {})
        return section_actions.get(action_type)

    def get_priority(self, section_name: str) -> int:
        """获取章节优先级"""
        return self.priority_rules.get(section_name, 999)

    def get_columns_for_sheet(self, sheet_name: str) -> List[str]:
        """获取指定 Sheet 的列定义"""
        mapping = self.sheet_column_mapping.get(sheet_name, {})
        return mapping.get('columns', [])

    def raw(self) -> Dict[str, Any]:
        """返回原始配置字典"""
        return self._config.copy()

    @classmethod
    def reset(cls) -> None:
        """重置单例（用于测试）"""
        cls._instance = None
