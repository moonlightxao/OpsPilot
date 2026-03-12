# -*- coding: utf-8 -*-
"""风险检测器测试"""

import pytest
from src.parser.risk_detector import RiskDetector, RiskAssessment
from src.parser.risk_keywords import (
    BUILTIN_RISK_KEYWORDS,
    SAFE_KEYWORDS,
    COMPOUND_RISK_PATTERNS
)


class TestRiskAssessment:
    """RiskAssessment 数据类测试"""

    def test_create_high_risk_assessment(self):
        """测试创建高危评估结果"""
        assessment = RiskAssessment(
            is_high_risk=True,
            risk_level="high",
            risk_score=90,
            risk_reasons=[{"type": "keyword_match", "keyword": "删除"}],
            source="builtin"
        )
        assert assessment.is_high_risk is True
        assert assessment.risk_level == "high"
        assert assessment.risk_score == 90
        assert assessment.source == "builtin"

    def test_create_safe_assessment(self):
        """测试创建安全评估结果"""
        assessment = RiskAssessment(
            is_high_risk=False,
            risk_level="safe",
            risk_score=10,
            risk_reasons=[],
            source="builtin"
        )
        assert assessment.is_high_risk is False
        assert assessment.risk_level == "safe"

    def test_create_assessment_minimal(self):
        """测试创建最小评估结果"""
        assessment = RiskAssessment(
            is_high_risk=False,
            risk_level="low",
            risk_score=30
        )
        assert assessment.risk_reasons == []
        assert assessment.source == "builtin"

    def test_create_assessment_with_multiple_reasons(self):
        """测试创建带多个原因的评估结果"""
        reasons = [
            {"type": "keyword_match", "keyword": "删除"},
            {"type": "compound_match", "keywords": ["批量", "删除"]}
        ]
        assessment = RiskAssessment(
            is_high_risk=True,
            risk_level="high",
            risk_score=95,
            risk_reasons=reasons
        )
        assert len(assessment.risk_reasons) == 2


class TestRiskDetector:
    """RiskDetector 测试"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.detector = RiskDetector()

    def test_init_default(self):
        """测试默认初始化"""
        detector = RiskDetector()
        assert len(detector.high_keywords) > 0
        assert len(detector.medium_keywords) > 0
        assert len(detector.safe_keywords) > 0
        assert len(detector.compound_patterns) > 0

    def test_init_with_config(self):
        """测试带配置初始化"""
        config = {
            "risk_detection": {
                "builtin": {
                    "custom_high_keywords": ["危险操作"],
                    "safe_keywords": ["安全操作"]
                }
            }
        }
        detector = RiskDetector(config)
        assert "危险操作" in detector.high_keywords
        assert "安全操作" in detector.safe_keywords

    # 高危关键词检测测试

    def test_assess_high_risk_keyword_delete(self):
        """测试高危关键词：删除"""
        result = self.detector.assess(action_type="删除", instruction="用户配置")
        assert result.is_high_risk is True
        assert result.risk_level == "high"
        assert result.risk_score >= 80

    def test_assess_high_risk_keyword_truncate(self):
        """测试高危关键词：truncate"""
        result = self.detector.assess(action_type="truncate", instruction="table")
        assert result.is_high_risk is True
        assert result.risk_level == "high"

    def test_assess_high_risk_keyword_drop(self):
        """测试高危关键词：drop"""
        result = self.detector.assess(action_type="drop", instruction="database")
        assert result.is_high_risk is True
        assert result.risk_level == "high"

    def test_assess_high_risk_keyword_offline(self):
        """测试高危关键词：下线"""
        result = self.detector.assess("下线", "服务实例")
        assert result.is_high_risk is True

    def test_assess_high_risk_keyword_rollback(self):
        """测试高危关键词：回滚"""
        result = self.detector.assess("回滚", "版本")
        assert result.is_high_risk is True

    # 中危关键词检测测试

    def test_assess_medium_risk_keyword_modify(self):
        """测试中危关键词：修改"""
        result = self.detector.assess("修改", "系统配置")
        assert result.risk_level in ["medium", "high"]
        assert result.risk_score >= 50

    def test_assess_medium_risk_keyword_change(self):
        """测试中危关键词：变更"""
        result = self.detector.assess("变更", "数据库结构")
        assert result.risk_level in ["medium", "high"]
        assert result.risk_score >= 50

    def test_assess_medium_risk_keyword_restart(self):
        """测试中危关键词：重启"""
        result = self.detector.assess("重启", "服务")
        assert result.risk_level in ["medium", "high"]
        assert result.risk_score >= 50

    # 安全关键词检测测试

    def test_assess_safe_keyword_backup(self):
        """测试安全关键词：备份"""
        result = self.detector.assess("备份", "数据库")
        assert result.risk_level == "safe"
        assert result.risk_score < 20

    def test_assess_safe_keyword_check(self):
        """测试安全关键词：检查"""
        result = self.detector.assess("检查", "配置")
        assert result.risk_level == "safe"
        assert result.is_high_risk is False

    def test_assess_safe_keyword_query(self):
        """测试安全关键词：查询"""
        result = self.detector.assess("查询", "数据")
        assert result.risk_level == "safe"

    def test_assess_safe_keyword_monitor(self):
        """测试安全关键词：监控"""
        result = self.detector.assess("监控", "服务状态")
        assert result.risk_level == "safe"

    # 组合风险模式测试

    def test_assess_compound_batch_delete(self):
        """测试组合模式：批量+删除"""
        result = self.detector.assess("批量删除", "生产数据")
        assert result.is_high_risk is True
        assert any(r["type"] == "compound_match" for r in result.risk_reasons)

    def test_assess_compound_production_delete(self):
        """测试组合模式：生产+删除"""
        result = self.detector.assess("删除", "生产环境配置")
        assert result.is_high_risk is True
        assert any(r["type"] == "compound_match" for r in result.risk_reasons)

    def test_assess_compound_master_modify(self):
        """测试组合模式：主库+修改"""
        result = self.detector.assess("修改", "主库配置")
        assert result.is_high_risk is True
        assert any(r["type"] == "compound_match" for r in result.risk_reasons)

    def test_assess_compound_restart_service(self):
        """测试组合模式：重启+服务"""
        result = self.detector.assess("重启服务", "")
        assert result.risk_level in ["medium", "high"]

    # 带单元格数据的评估测试

    def test_assess_with_cells_multiple(self):
        """测试带多个单元格数据的评估"""
        result = self.detector.assess(
            action_type="删除",
            instruction="",
            cells=["配置1", "配置2", "配置3", "配置4", "配置5"]
        )
        assert result.is_high_risk is True
        assert result.risk_score >= 80

    def test_assess_with_cells_safe(self):
        """测试带安全单元格数据的评估"""
        result = self.detector.assess(
            action_type="备份",
            instruction="",
            cells=["配置1", "配置2"]
        )
        assert result.risk_level == "safe"

    # 分数到等级转换测试

    def test_score_to_level_high(self):
        """测试分数转等级：high"""
        assert self.detector._score_to_level(100) == "high"
        assert self.detector._score_to_level(90) == "high"
        assert self.detector._score_to_level(80) == "high"

    def test_score_to_level_medium(self):
        """测试分数转等级：medium"""
        assert self.detector._score_to_level(79) == "medium"
        assert self.detector._score_to_level(60) == "medium"
        assert self.detector._score_to_level(50) == "medium"

    def test_score_to_level_low(self):
        """测试分数转等级：low"""
        assert self.detector._score_to_level(49) == "low"
        assert self.detector._score_to_level(30) == "low"
        assert self.detector._score_to_level(20) == "low"

    def test_score_to_level_safe(self):
        """测试分数转等级：safe"""
        assert self.detector._score_to_level(19) == "safe"
        assert self.detector._score_to_level(10) == "safe"
        assert self.detector._score_to_level(0) == "safe"

    # 自定义关键词测试

    def test_custom_high_keywords(self):
        """测试自定义高危关键词"""
        config = {
            "risk_detection": {
                "builtin": {
                    "custom_high_keywords": ["危险操作", "紧急下线"]
                }
            }
        }
        detector = RiskDetector(config)
        result = detector.assess("危险操作", "")
        assert result.is_high_risk is True

    def test_custom_medium_keywords(self):
        """测试自定义中危关键词"""
        config = {
            "risk_detection": {
                "builtin": {
                    "custom_medium_keywords": ["调整配置"]
                }
            }
        }
        detector = RiskDetector(config)
        result = detector.assess("调整配置", "")
        assert result.risk_level in ["medium", "high"]

    def test_custom_safe_keywords(self):
        """测试自定义安全关键词"""
        config = {
            "risk_detection": {
                "builtin": {
                    "safe_keywords": ["安全审计"]
                }
            }
        }
        detector = RiskDetector(config)
        result = detector.assess("安全审计", "")
        assert result.risk_level == "safe"

    # 自定义组合规则测试

    def test_custom_compound_rules(self):
        """测试自定义组合规则"""
        config = {
            "risk_detection": {
                "compound_rules": [
                    {"keywords": ["紧急", "修复"], "level": "high", "score": 85}
                ]
            }
        }
        detector = RiskDetector(config)
        result = detector.assess("紧急修复", "数据库")
        assert result.risk_score >= 85

    def test_multiple_custom_compound_rules(self):
        """测试多个自定义组合规则"""
        config = {
            "risk_detection": {
                "compound_rules": [
                    {"keywords": ["测试", "删除"], "level": "medium", "score": 40},
                    {"keywords": ["生产", "删除"], "level": "high", "score": 95}
                ]
            }
        }
        detector = RiskDetector(config)

        result1 = detector.assess("测试删除", "数据")
        assert result1.risk_score >= 40

        result2 = detector.assess("生产删除", "数据")
        assert result2.risk_score >= 95

    # 边界情况测试

    def test_assess_empty_input(self):
        """测试空输入"""
        result = self.detector.assess("", "")
        assert result.risk_level == "safe"
        assert result.is_high_risk is False

    def test_assess_none_cells(self):
        """测试 None 单元格"""
        result = self.detector.assess("删除", "", cells=None)
        assert result.is_high_risk is True

    def test_assess_empty_cells(self):
        """测试空单元格列表"""
        result = self.detector.assess("删除", "", cells=[])
        assert result.is_high_risk is True

    def test_assess_cells_with_none_values(self):
        """测试包含 None 值的单元格"""
        result = self.detector.assess(
            "删除",
            "",
            cells=["配置1", None, "", "配置2"]
        )
        assert result.is_high_risk is True

    # 风险原因详情测试

    def test_risk_reasons_include_keyword(self):
        """测试风险原因包含匹配的关键词"""
        result = self.detector.assess("删除", "配置")
        assert any(
            r["type"] == "keyword_match" and r["keyword"] == "删除"
            for r in result.risk_reasons
        )

    def test_risk_reasons_include_compound(self):
        """测试风险原因包含组合匹配"""
        result = self.detector.assess("批量删除", "数据")
        assert any(
            r["type"] == "compound_match"
            for r in result.risk_reasons
        )

    def test_risk_reasons_source(self):
        """测试风险来源标识"""
        result = self.detector.assess("删除", "配置")
        assert result.source == "builtin"

    # 混合场景测试

    def test_safe_keyword_overrides_risk(self):
        """测试安全关键词覆盖风险"""
        result = self.detector.assess("备份删除", "策略")
        # 安全关键词优先，返回 safe
        assert result.risk_level == "safe"

    def test_instruction_with_risk_keyword(self):
        """测试指令中包含风险关键词"""
        result = self.detector.assess("配置", "删除所有数据")
        assert result.is_high_risk is True

    def test_cells_with_risk_keyword(self):
        """测试单元格中包含风险关键词"""
        result = self.detector.assess(
            "配置",
            "更新参数",
            cells=["删除旧文件", "清理缓存"]
        )
        assert result.is_high_risk is True


class TestRiskKeywords:
    """风险关键词库测试"""

    def test_high_keywords_exist(self):
        """测试高危关键词存在"""
        assert "high" in BUILTIN_RISK_KEYWORDS
        assert "keywords" in BUILTIN_RISK_KEYWORDS["high"]
        assert "score" in BUILTIN_RISK_KEYWORDS["high"]
        assert "category" in BUILTIN_RISK_KEYWORDS["high"]
        assert len(BUILTIN_RISK_KEYWORDS["high"]["keywords"]) > 0

    def test_medium_keywords_exist(self):
        """测试中危关键词存在"""
        assert "medium" in BUILTIN_RISK_KEYWORDS
        assert "keywords" in BUILTIN_RISK_KEYWORDS["medium"]
        assert "score" in BUILTIN_RISK_KEYWORDS["medium"]
        assert len(BUILTIN_RISK_KEYWORDS["medium"]["keywords"]) > 0

    def test_low_keywords_exist(self):
        """测试低危关键词存在"""
        assert "low" in BUILTIN_RISK_KEYWORDS
        assert "keywords" in BUILTIN_RISK_KEYWORDS["low"]
        assert "score" in BUILTIN_RISK_KEYWORDS["low"]
        assert len(BUILTIN_RISK_KEYWORDS["low"]["keywords"]) > 0

    def test_keyword_scores(self):
        """测试关键词分数"""
        assert BUILTIN_RISK_KEYWORDS["high"]["score"] >= 80
        assert BUILTIN_RISK_KEYWORDS["medium"]["score"] >= 50
        assert BUILTIN_RISK_KEYWORDS["low"]["score"] >= 20

    def test_keyword_categories(self):
        """测试关键词分类"""
        assert BUILTIN_RISK_KEYWORDS["high"]["category"] == "destructive"
        assert BUILTIN_RISK_KEYWORDS["medium"]["category"] == "impactful"
        assert BUILTIN_RISK_KEYWORDS["low"]["category"] == "routine"

    def test_safe_keywords_exist(self):
        """测试安全关键词存在"""
        assert len(SAFE_KEYWORDS) > 0
        assert "备份" in SAFE_KEYWORDS
        assert "backup" in SAFE_KEYWORDS

    def test_compound_patterns_exist(self):
        """测试组合模式存在"""
        assert len(COMPOUND_RISK_PATTERNS) > 0
        for pattern in COMPOUND_RISK_PATTERNS:
            assert isinstance(pattern, tuple)
            assert len(pattern) == 3
            assert isinstance(pattern[0], list)  # keywords
            assert isinstance(pattern[1], str)     # level
            assert isinstance(pattern[2], int)     # score

    def test_compound_patterns_content(self):
        """测试组合模式内容"""
        # 批量删除应该是高危
        batch_delete = [p for p in COMPOUND_RISK_PATTERNS if "批量" in p[0] and "删除" in p[0]]
        assert len(batch_delete) > 0
        assert batch_delete[0][1] == "high"
        assert batch_delete[0][2] >= 90

    def test_common_high_keywords(self):
        """测试常见高危关键词"""
        keywords = BUILTIN_RISK_KEYWORDS["high"]["keywords"]
        assert "删除" in keywords
        assert "delete" in keywords
        assert "truncate" in keywords
        assert "drop" in keywords

    def test_common_medium_keywords(self):
        """测试常见中危关键词"""
        keywords = BUILTIN_RISK_KEYWORDS["medium"]["keywords"]
        assert "修改" in keywords
        assert "变更" in keywords
        assert "modify" in keywords
        assert "change" in keywords

    def test_common_safe_keywords(self):
        """测试常见安全关键词"""
        assert "备份" in SAFE_KEYWORDS
        assert "检查" in SAFE_KEYWORDS
        assert "查询" in SAFE_KEYWORDS
        assert "backup" in SAFE_KEYWORDS
        assert "check" in SAFE_KEYWORDS
