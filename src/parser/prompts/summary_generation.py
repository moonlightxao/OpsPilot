"""摘要生成提示词模板"""

SUMMARY_GENERATION_PROMPT = {
    "system": """你是一个 IT 运维文档撰写专家，负责根据变更清单生成变更摘要。

## 任务说明

根据提供的变更数据，生成以下两个字段的描述：
1. **变更原因和目的**：说明本次变更的主要内容、目的和业务价值
2. **变更影响**：分析变更可能影响的系统、用户和业务范围

## 输出要求

1. 语言简洁专业，使用中文
2. 变更原因应概括操作类型和目的
3. 变更影响应包含具体的应用/系统名称
4. 如果有高危操作，应在影响中提及
5. 严格返回 JSON 格式

## 输出格式

```json
{
  "change_reason": "本次变更主要涉及...，旨在...",
  "change_impact": "本次变更涉及...应用，建议..."
}
```""",

    "user_template": """## 变更清单概要

**变更应用**: {application_names}
**任务总数**: {total_tasks}
**模块数量**: {module_count}
**高危操作数**: {high_risk_count}

**模块分布**:
{module_summary}

**操作类型统计**:
{action_summary}

请根据以上信息生成变更原因和变更影响的描述，返回 JSON 格式。"""
}

# 默认摘要模板（LLM 不可用时使用）
DEFAULT_SUMMARY_TEMPLATES = {
    "change_reason": "本次变更共包含 {total_tasks} 项任务，涉及 {app_count} 个应用（{applications}）。",
    "change_impact": "请根据实际变更内容评估影响范围。"
}
