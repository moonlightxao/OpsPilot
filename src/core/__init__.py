"""
OpsPilot 核心层

提供领域模型和统一配置管理。
"""

from .config_manager import ConfigManager
from .domain import Task, ActionGroup, Section, ImplementationSummary, RiskAlert, ReportMeta, ReportSummary

__all__ = [
    "ConfigManager",
    "Task",
    "ActionGroup",
    "Section",
    "ImplementationSummary",
    "RiskAlert",
    "ReportMeta",
    "ReportSummary",
]
