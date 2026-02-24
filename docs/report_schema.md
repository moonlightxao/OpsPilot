# report.json 数据协议规范 (v2.1 - 输出与样例对齐)

## 概述
`report.json` 是解析层（Parser）与渲染层（Renderer）之间的中间态数据结构。
**v2.0 变更**：适配 `docxtpl` 模板引擎，结构设计支持 Jinja2 `{% for %}` 循环。
**v2.1 变更**：新增 `implementation_summary` 字段，支持第2章「实施总表」独立输出。

## 设计原则（docxtpl 适配）

1. **层级扁平化**：避免深层嵌套，便于模板循环
2. **列数据前置**：表格列名作为上下文传入，而非动态推断
3. **高危标记外置**：`is_high_risk` 字段用于模板条件渲染

## JSON Schema

```json
{
  "meta": {
    "source_file": "string - 原始 Excel 文件名",
    "generated_at": "string - ISO 8601 时间戳",
    "version": "string - 协议版本号，当前为 2.0"
  },
  "summary": {
    "total_tasks": "integer - 任务总数",
    "total_sheets": "integer - 解析的 Sheet 数量",
    "high_risk_count": "integer - 高危操作数量",
    "has_external_links": "boolean - 是否有外部链接",
    "external_links": ["string - 外部链接 URL 列表"]
  },
  "has_risk_alerts": "boolean - 是否存在风险告警",
  "risk_alerts": [
    {
      "sheet_name": "string - 所属 Sheet 名",
      "action_type": "string - 触发的高危操作类型",
      "task_count": "integer - 涉及任务数",
      "task_names": ["string - 涉及的任务名列表"]
    }
  ],
  "implementation_summary": {
    "sheet_name": "string - 源 Sheet 名称",
    "columns": ["string - 表头列名"],
    "rows": [
      { "cells": ["string - 按列顺序的单元格值"] }
    ],
    "has_data": "boolean - 是否有数据"
  },
  "sections": [
    {
      "section_name": "string - 章节/Sheet 名称",
      "priority": "integer - 章节优先级",
      "has_action_groups": "boolean - 是否有操作组",
      "columns": ["string - 该章节表格的列名列表"],
      "action_groups": [
        {
          "action_type": "string - 操作类型",
          "instruction": "string - 操作说明文本",
          "is_high_risk": "boolean - 是否高危操作",
          "task_count": "integer - 任务数量",
          "tasks": [
            {
              "cells": ["string - 按列顺序排列的单元格值"]
            }
          ]
        }
      ]
    }
  ]
}
```

## 模板映射关系

### Jinja2 循环结构

```jinja2
{# 遍历章节 #}
{% for section in sections %}
  {{ section.section_name }}

  {# 遍历操作组 #}
  {% for action_group in section.action_groups %}
    {{ action_group.action_type }}
    {{ action_group.instruction }}

    {# 遍历表格行 #}
    {% for task in action_group.tasks %}
      {% for cell in task.cells %}{{ cell }}{% endfor %}
    {% endfor %}
  {% endfor %}
{% endfor %}
```

### 条件渲染

```jinja2
{# 高危标记 #}
{% if action_group.is_high_risk %}
  【高危操作】
{% endif %}

{# 风险告警区块 #}
{% if has_risk_alerts %}
  {% for alert in risk_alerts %}
    {{ alert.action_type }} - {{ alert.task_count }} 个任务
  {% endfor %}
{% endif %}
```

## 示例数据

```json
{
  "meta": {
    "source_file": "上线checklist.xlsx",
    "generated_at": "2026-02-22T10:00:00Z",
    "version": "2.0"
  },
  "summary": {
    "total_tasks": 5,
    "total_sheets": 2,
    "high_risk_count": 1,
    "has_external_links": true,
    "external_links": ["http://wiki.internal/procedure"]
  },
  "has_risk_alerts": true,
  "risk_alerts": [
    {
      "sheet_name": "应用配置",
      "action_type": "删除",
      "task_count": 1,
      "task_names": ["废弃配置清理"]
    }
  ],
  "sections": [
    {
      "section_name": "数据库脚本部署",
      "priority": 10,
      "has_action_groups": true,
      "columns": ["脚本名称", "执行顺序", "数据库", "执行人", "备注"],
      "action_groups": [
        {
          "action_type": "新增",
          "instruction": "在配置管理中心，点击新增按钮，新增以下配置：",
          "is_high_risk": false,
          "task_count": 2,
          "tasks": [
            {"cells": ["用户表扩展.sql", "1", "user_db", "张三", ""]},
            {"cells": ["订单索引.sql", "2", "order_db", "李四", "优化查询"]}
          ]
        }
      ]
    },
    {
      "section_name": "应用配置",
      "priority": 20,
      "has_action_groups": true,
      "columns": ["配置项", "配置值", "所属应用", "执行人", "备注"],
      "action_groups": [
        {
          "action_type": "新增",
          "instruction": "在配置管理中心，点击新增按钮，新增以下配置：",
          "is_high_risk": false,
          "task_count": 1,
          "tasks": [
            {"cells": ["max_connections", "500", "app-server", "王五", ""]}
          ]
        },
        {
          "action_type": "删除",
          "instruction": "【高危操作】在配置管理中心，定位以下配置项并删除：",
          "is_high_risk": true,
          "task_count": 1,
          "tasks": [
            {"cells": ["deprecated_flag", "true", "legacy-app", "王五", "已废弃"]}
          ]
        }
      ]
    }
  ]
}
```

## v2.0 → v2.1 变更说明

| 变更项 | v2.0 | v2.1 | 原因 |
|--------|------|------|------|
| 实施总表 | 无 | `implementation_summary` | PRD 要求 Sheet 1 作为第2章主体表格输出 |

## v2.1 实施总表列规范（2026-02-23 修订）

与 `实施文档.docx` 样例一致，`implementation_summary.columns` 固定为 6 列（顺序不可变）：
`序号` | `任务` | `开始时间` | `结束时间` | `实施人` | `复核人`

- **日期列**：`开始时间`、`结束时间` 须为可读格式 `YYYY-MM-DD`，Parser 负责将 Excel 序列号（如 46315）转换
- **未命名列**：Parser 须过滤 `Unnamed`、空列名，不输出
- **列映射**：由 rules.yaml `implementation_summary.column_mapping` 驱动

## v1.0 → v2.0 变更说明

| 变更项 | v1.0 | v2.0 | 原因 |
|--------|------|------|------|
| 任务字段 | `raw_data` 对象 | `cells` 数组 | 模板按索引访问更简洁 |
| 列定义 | 动态从 config 读取 | `section.columns` 前置 | 模板渲染时已知列名 |
| 高危判断 | 遍历检查 | `is_high_risk` 布尔值 | 支持模板 `{% if %}` |
| 存在性标记 | 无 | `has_risk_alerts`, `has_external_links` | 模板条件渲染优化 |

## 字段说明

| 字段路径 | 必填 | 说明 |
|----------|------|------|
| `meta.version` | Y | 协议版本，当前为 "2.0" 或 "2.1" |
| `implementation_summary.sheet_name` | Y | 实施总表源 Sheet 名称 |
| `implementation_summary.columns` | Y | 实施总表表头 |
| `implementation_summary.rows` | Y | 实施总表数据行 |
| `implementation_summary.has_data` | Y | 是否有实施总表数据，用于模板条件渲染 |
| `summary.has_external_links` | Y | 用于模板条件渲染外部链接区块 |
| `has_risk_alerts` | Y | 用于模板条件渲染风险告警区块 |
| `sections[].columns` | Y | 该章节表格的列名，用于表头渲染 |
| `sections[].has_action_groups` | Y | 用于模板条件判断 |
| `action_groups[].task_count` | Y | 任务数量，便于统计显示 |
| `tasks[].cells` | Y | 按列顺序排列的单元格值数组 |
