"""
领域模型定义

定义 Parser 和 Renderer 共用的核心数据结构，与 report_schema.md v2.2 保持兼容。
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Task:
    """任务领域模型"""
    task_name: str = ""
    deploy_unit: str = ""
    executor: str = ""
    external_link: str = ""
    cells: List[str] = field(default_factory=list)
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionGroup:
    """操作组领域模型"""
    action_type: str = ""
    instruction: str = ""
    is_high_risk: bool = False
    tasks: List[Task] = field(default_factory=list)

    @property
    def task_count(self) -> int:
        return len(self.tasks)


@dataclass
class Section:
    """章节领域模型"""
    section_name: str = ""
    priority: int = 999
    columns: List[str] = field(default_factory=list)
    action_groups: List[ActionGroup] = field(default_factory=list)

    @property
    def has_action_groups(self) -> bool:
        return len(self.action_groups) > 0

    @property
    def task_count(self) -> int:
        return sum(ag.task_count for ag in self.action_groups)


@dataclass
class ImplementationSummary:
    """实施总表领域模型"""
    sheet_name: str = ""
    columns: List[str] = field(default_factory=list)
    rows: List[Dict[str, Any]] = field(default_factory=list)
    has_data: bool = False


@dataclass
class RiskAlert:
    """风险告警领域模型"""
    sheet_name: str = ""
    action_type: str = ""
    risk_level: str = "safe"
    risk_score: int = 0
    source: str = "builtin"
    risk_reasons: List[Dict[str, Any]] = field(default_factory=list)
    task_count: int = 0
    task_names: List[str] = field(default_factory=list)


@dataclass
class ReportMeta:
    """报告元数据领域模型"""
    source_file: str = ""
    generated_at: str = ""
    version: str = "2.2"
    application_name: str = ""
    change_reason: str = ""
    change_impact: str = ""


@dataclass
class ReportSummary:
    """报告摘要领域模型"""
    total_tasks: int = 0
    total_sheets: int = 0
    high_risk_count: int = 0
    has_external_links: bool = False
    external_links: List[str] = field(default_factory=list)
