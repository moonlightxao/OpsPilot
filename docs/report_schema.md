# report.json 数据协议规范

## 概述
`report.json` 是解析层（Parser）与渲染层（Renderer）之间的中间态数据结构。
所有字段设计确保能被 LLM 清晰理解，支持人工确认流程。

## JSON Schema

```json
{
  "meta": {
    "source_file": "string - 原始 Excel 文件名",
    "generated_at": "string - ISO 8601 时间戳",
    "version": "string - 协议版本号"
  },
  "summary": {
    "total_tasks": "integer - 任务总数",
    "total_sheets": "integer - 解析的 Sheet 数量",
    "high_risk_count": "integer - 高危操作数量",
    "external_links": ["string - 所有提取的外部链接 URL"]
  },
  "risk_alerts": [
    {
      "sheet_name": "string - 所属 Sheet 名",
      "action_type": "string - 触发的高危操作类型",
      "task_count": "integer - 涉及任务数",
      "task_names": ["string - 涉及的任务名列表"]
    }
  ],
  "sections": [
    {
      "section_name": "string - 章节/Sheet 名称",
      "priority": "integer - 章节优先级（来自 rules.yaml）",
      "action_groups": [
        {
          "action_type": "string - 操作类型",
          "instruction": "string - 操作说明文本（来自 action_library）",
          "is_high_risk": "boolean - 是否高危操作",
          "tasks": [
            {
              "task_name": "string - 任务名",
              "deploy_unit": "string - 部署单元",
              "executor": "string - 执行人",
              "external_link": "string - 外部链接",
              "raw_data": "object - 原始行数据的完整字典"
            }
          ]
        }
      ]
    }
  ]
}
```

## 示例数据

```json
{
  "meta": {
    "source_file": "上线checklist.xlsx",
    "generated_at": "2026-02-17T15:30:00Z",
    "version": "1.0.0"
  },
  "summary": {
    "total_tasks": 25,
    "total_sheets": 4,
    "high_risk_count": 2,
    "external_links": [
      "http://wiki.internal/procedure/db-deploy",
      "http://config-center/app-settings"
    ]
  },
  "risk_alerts": [
    {
      "sheet_name": "应用配置",
      "action_type": "删除",
      "task_count": 2,
      "task_names": ["废弃配置清理-ItemA", "废弃配置清理-ItemB"]
    }
  ],
  "sections": [
    {
      "section_name": "数据库脚本部署",
      "priority": 10,
      "action_groups": [
        {
          "action_type": "新增",
          "instruction": "在配置管理中心，点击新增按钮，新增以下配置：",
          "is_high_risk": false,
          "tasks": [
            {
              "task_name": "用户表字段扩展",
              "deploy_unit": "user_db",
              "executor": "张三",
              "external_link": "http://wiki.internal/procedure/db-deploy",
              "raw_data": {
                "任务名": "用户表字段扩展",
                "操作类型": "新增",
                "数据库": "user_db",
                "执行人": "张三"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

## 字段说明

| 字段路径 | 必填 | 说明 |
|---------|------|------|
| `meta.source_file` | Y | 源文件名，用于溯源 |
| `meta.generated_at` | Y | 生成时间，用于审计 |
| `meta.version` | Y | 协议版本，便于兼容性处理 |
| `summary.total_tasks` | Y | 任务统计，供人工确认时快速浏览 |
| `summary.high_risk_count` | Y | 高危数量，用于风险提示 |
| `summary.external_links` | N | 链接集合，供时效性检查 |
| `risk_alerts[]` | N | 风险告警列表，仅当存在高危操作时填充 |
| `sections[]` | Y | 章节数据，按 priority 排序 |
| `sections[].action_groups[]` | Y | 聚合后的操作组，相同 action 合并 |
| `tasks[].raw_data` | Y | 原始行数据，保留所有列以支持动态表头 |
