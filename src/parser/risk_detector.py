# -*- coding: utf-8 -*-
"""
智能风险检测器 - 内置词库 + LLM 增强

提供操作风险评估功能，支持基于内置关键词库的快速检测
和基于 LLM 的深度语义分析。
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from .risk_keywords import (
    BUILTIN_RISK_KEYWORDS,
    SAFE_KEYWORDS,
    COMPOUND_RISK_PATTERNS
)


@dataclass
class RiskAssessment:
    """风险评估结果"""
    is_high_risk: bool
    risk_level: str        # "high" | "medium" | "low" | "safe"
    risk_score: int        # 0-100
    risk_reasons: List[Dict[str, Any]] = field(default_factory=list)
    source: str = "builtin"  # "builtin" | "llm"


class RiskDetector:
    """智能风险识别器 - 内置词库 + LLM 增强"""

    def __init__(self, config: dict = None, llm_client=None):
        """
        初始化风险检测器

        Args:
            config: 配置字典，可包含自定义关键词
            llm_client: LLM 客户端实例（可选）
        """
        self.config = config or {}
        self.llm_client = llm_client
        self._load_keywords()

    def _load_keywords(self):
        """加载关键词配置"""
        # 从配置加载自定义关键词
        risk_config = self.config.get("risk_detection", {})
        builtin_config = risk_config.get("builtin", {})

        # 合并自定义关键词
        self.high_keywords = list(BUILTIN_RISK_KEYWORDS["high"]["keywords"])
        self.medium_keywords = list(BUILTIN_RISK_KEYWORDS["medium"]["keywords"])
        self.low_keywords = list(BUILTIN_RISK_KEYWORDS["low"]["keywords"])
        self.safe_keywords = list(SAFE_KEYWORDS)

        # 扩展关键词
        self.high_keywords.extend(builtin_config.get("custom_high_keywords", []))
        self.medium_keywords.extend(builtin_config.get("custom_medium_keywords", []))
        self.safe_keywords.extend(builtin_config.get("safe_keywords", []))

        # 加载组合规则
        self.compound_patterns = list(COMPOUND_RISK_PATTERNS)
        for rule in risk_config.get("compound_rules", []):
            self.compound_patterns.append((
                rule["keywords"],
                rule["level"],
                rule["score"]
            ))

    def assess(
        self,
        action_type: str,
        instruction: str = "",
        cells: List[Any] = None,
        use_llm: bool = False
    ) -> RiskAssessment:
        """
        评估操作风险

        Args:
            action_type: 操作类型（如 "删除"、"新增"）
            instruction: 操作说明文本
            cells: 单元格数据列表
            use_llm: 是否使用 LLM 深度分析

        Returns:
            RiskAssessment 风险评估结果
        """
        # 1. 内置词库快速筛选
        builtin_result = self._builtin_assess(action_type, instruction, cells)

        # 2. 如果已识别为高危，直接返回
        if builtin_result.is_high_risk:
            return builtin_result

        # 3. 可选：LLM 深度分析
        if use_llm and self.llm_client:
            return self._llm_assess(action_type, instruction, cells, builtin_result)

        return builtin_result

    def _builtin_assess(
        self,
        action_type: str,
        instruction: str,
        cells: List[Any]
    ) -> RiskAssessment:
        """内置词库评估"""
        reasons = []
        max_score = 0

        # 合并待分析文本
        texts = [action_type, instruction]
        if cells:
            texts.extend(str(c) for c in cells if c)
        combined_text = " ".join(texts).lower()

        # 检查安全关键词白名单
        for kw in self.safe_keywords:
            if kw.lower() in combined_text:
                # 白名单关键词存在，降低风险等级
                return RiskAssessment(
                    is_high_risk=False,
                    risk_level="safe",
                    risk_score=10,
                    risk_reasons=[{
                        "type": "safe_keyword",
                        "keyword": kw,
                        "category": "whitelist"
                    }],
                    source="builtin"
                )

        # 高危关键词匹配
        for kw in self.high_keywords:
            if kw.lower() in combined_text:
                reasons.append({
                    "type": "keyword_match",
                    "keyword": kw,
                    "category": "destructive",
                    "level": "high"
                })
                max_score = max(max_score, 90)

        # 中危关键词匹配
        for kw in self.medium_keywords:
            if kw.lower() in combined_text:
                reasons.append({
                    "type": "keyword_match",
                    "keyword": kw,
                    "category": "impactful",
                    "level": "medium"
                })
                max_score = max(max_score, 60)

        # 低危关键词匹配
        for kw in self.low_keywords:
            if kw.lower() in combined_text:
                reasons.append({
                    "type": "keyword_match",
                    "keyword": kw,
                    "category": "routine",
                    "level": "low"
                })
                max_score = max(max_score, 30)

        # 组合风险模式
        for keywords, level, score in self.compound_patterns:
            if all(kw.lower() in combined_text for kw in keywords):
                reasons.append({
                    "type": "compound_match",
                    "keywords": keywords,
                    "category": "compound_risk",
                    "level": level
                })
                max_score = max(max_score, score)

        # 确定风险等级
        risk_level = self._score_to_level(max_score)

        return RiskAssessment(
            is_high_risk=(risk_level == "high"),
            risk_level=risk_level,
            risk_score=max_score,
            risk_reasons=reasons,
            source="builtin"
        )

    def _llm_assess(
        self,
        action_type: str,
        instruction: str,
        cells: List[Any],
        builtin_result: RiskAssessment
    ) -> RiskAssessment:
        """LLM 深度分析（延迟导入避免循环依赖）"""
        try:
            from .llm_risk_analyzer import LLMRiskAnalyzer, OperationContext

            analyzer = LLMRiskAnalyzer(self.llm_client)
            context = OperationContext(
                sheet_name="",
                action_type=action_type,
                instruction=instruction,
                sample_tasks=[{"cells": cells}] if cells else []
            )
            result = analyzer.analyze(context)

            # LLM 结果优先
            return RiskAssessment(
                is_high_risk=result.get("risk_level") == "high",
                risk_level=result.get("risk_level", builtin_result.risk_level),
                risk_score=result.get("risk_score", builtin_result.risk_score),
                risk_reasons=result.get("risk_reasons", builtin_result.risk_reasons),
                source="llm"
            )
        except Exception as e:
            # LLM 调用失败，回退到内置结果
            builtin_result.risk_reasons.append({
                "type": "llm_error",
                "message": str(e)
            })
            return builtin_result

    def _score_to_level(self, score: int) -> str:
        """分数转等级"""
        if score >= 80:
            return "high"
        elif score >= 50:
            return "medium"
        elif score >= 20:
            return "low"
        return "safe"
