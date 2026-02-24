# 技术方案：输出与样例对齐（修订版 v2）

**文档版本**: 2.0  
**修订日期**: 2026-02-23  
**状态**: 待 Developer 实现  
**负责人**: Architect  
**修订原因**: PM 验收发现产出与 `实施文档.docx` 标准严重不符，需明确修正路径

---

## 1. 需求与缺陷对照

### 1.1 核心目标（不变）
- 实施总表来自 Excel Sheet 1，输出至第2章主体位置
- 章节结构、表格形式、排版样式与样例可视觉比对一致
- 逻辑闭环、聚合正确、安全拦截

### 1.2 PM 验收缺陷（需修正）

| 缺陷项 | 标准文档 (Sample) | 当前产出 | 修正方向 |
|--------|-------------------|----------|----------|
| **第1部分缺失** | 1 原因和目的、1.1 变更应用、1.2 变更原因和目的、1.3 变更影响 | 完全缺失 | 模板增加第1部分区块 |
| **第2部分结构错误** | 2 实施步骤和计划 → 2.1 详细实施步骤 → 2.1.1～2.1.5 子章节 | 2.1 实施总表、2.2 详细步骤 | 调整层级与编号 |
| **实施总表表格异常** | 列：序号\|任务\|开始时间\|结束时间\|实施人\|复核人 | 46315、Unnamed:6 等 | 列映射 + 日期转换 + 过滤未命名列 |
| **详细步骤结构不符** | 2.1.1、2.1.2… 子节 + 操作说明 + 任务表格 | 无编号的平铺 section | 章节编号 2.1.1～2.1.N |
| **第3～5部分** | 3 实施后验证计划、4 应急回退措施、5 风险分析 | 缺失 | 模板增加预留区块 |

---

## 2. 修正技术方案

### 2.1 目标文档结构（与样例一致）

```
文档标题：{{ title }}

【第1部分】1 原因和目的
  1.1 变更应用
    （占位或 meta.application_name）
  1.2 变更原因和目的
    （占位或 meta.change_reason）
  1.3 变更影响
    （占位或 meta.change_impact）

【第2部分】2 实施步骤和计划
  [实施总表]（表格，无 2.x 编号，为主体内容）
    列：序号 | 任务 | 开始时间 | 结束时间 | 实施人 | 复核人
  2.1 详细实施步骤（二级标题）
    2.1.1 《section_1 名称》（如：数据库脚本部署）
      操作说明 + 任务表格
    2.1.2 《section_2 名称》
      ...
    2.1.N 《section_N 名称》

【第3部分】3 实施后验证计划
  （预留标准模版内容）

【第4部分】4 应急回退措施
  （预留标准模版内容）

【第5部分】5 风险分析和规避措施
  （预留标准模版内容）

【附录】摘要信息、风险告警、外部链接
  （可保留在文档末尾，或按样例位置调整）
```

**说明**：实施总表在「2 实施步骤和计划」下、2.1 之前，作为无编号的主体表格；详细步骤使用 2.1.1、2.1.2… 作为各 section 的编号。

---

### 2.2 实施总表列映射与清洗

**标准输出列**（与样例一致）：
| 列序号 | 列名 | 说明 |
|--------|------|------|
| 1 | 序号 | 行号或 Excel 原序号 |
| 2 | 任务 | 任务名称 |
| 3 | 开始时间 | 日期，格式 YYYY-MM-DD |
| 4 | 结束时间 | 日期，格式 YYYY-MM-DD |
| 5 | 实施人 | 执行人 |
| 6 | 复核人 | 复核人 |

**Excel 常见列名别名**（需在 rules 中配置映射）：
- 任务：任务名、任务名称、任务、Task
- 开始时间：开始时间、开始日期、计划开始
- 结束时间：结束时间、结束日期、计划结束
- 实施人：实施人、执行人、负责人
- 复核人：复核人、复核、审核人

**Parser 修正**：
1. **过滤未命名列**：`Unnamed`、空列名不进入 columns/rows
2. **Excel 日期转换**：对 `开始时间`、`结束时间` 列，若值为 Excel 序列号（整数如 46315），则转为 `YYYY-MM-DD`
3. **列映射**：按 rules 中 `implementation_summary.column_mapping` 将 Excel 列映射到标准 6 列；未配置则按别名智能匹配
4. **序号列**：若 Excel 无「序号」列，则自动生成 1、2、3…

---

### 2.3 rules.yaml 配置扩展

```yaml
implementation_summary:
  strategy: "first_sheet"
  sheet_names: ["上线安排", "实施总表"]
  # 标准输出列（与样例一致，固定顺序）
  output_columns: ["序号", "任务", "开始时间", "结束时间", "实施人", "复核人"]
  # Excel 列名 -> 标准列名 映射（支持多对一取第一个匹配）
  column_mapping:
    "任务": ["任务名", "任务名称", "任务", "Task"]
    "开始时间": ["开始时间", "开始日期", "计划开始"]
    "结束时间": ["结束时间", "结束日期", "计划结束"]
    "实施人": ["实施人", "执行人", "负责人"]
    "复核人": ["复核人", "复核", "审核人"]
  # 需做 Excel 日期序列号转换的列
  date_columns: ["开始时间", "结束时间"]
  # 是否自动生成序号列（当 Excel 无该列时）
  auto_sequence: true
  # 是否过滤 Unnamed / 空列名
  drop_unnamed_columns: true
```

---

### 2.4 report.json 协议（不变）

`implementation_summary` 结构保持 v2.1，但 `columns` 与 `rows.cells` 必须按 `output_columns` 顺序输出，且日期已转为可读格式。

---

### 2.5 模板 (template.docx) 修正路径

| 区块 | 修正内容 |
|------|----------|
| **第1部分** | 在文档标题后、摘要前，增加「1 原因和目的」及 1.1、1.2、1.3 占位段落；可使用 `meta.application_name` 等（若 report 扩展）或固定占位文案 |
| **第2部分** | 2 实施步骤和计划 → [实施总表表格，固定 6 列] → 2.1 详细实施步骤 → `{% for section in sections %}` 输出 2.1.{{ loop.index }} + section.section_name + 操作组+表格 |
| **第3～5部分** | 在 sections 循环结束后，增加「3 实施后验证计划」「4 应急回退措施」「5 风险分析和规避措施」三级标题及预留占位段落 |
| **实施总表表格** | 固定 6 列：序号、任务、开始时间、结束时间、实施人、复核人；使用 `implementation_summary.columns` 与 `rows`（Parser 保证顺序一致） |
| **详细步骤编号** | section 循环使用 `2.1.{{ loop.index }}` 作为子节编号 |

---

### 2.6 create_template.py 修正

1. 在「文档标题」后插入第1部分区块
2. 调整第2部分：2 实施步骤和计划 → 实施总表（6 列）→ 2.1 详细实施步骤
3. 实施总表表格列数改为 6，列名来自 `output_columns` 或 `implementation_summary.columns`
4. section 标题改为 `2.1.{{ loop.index }} {{ section.section_name }}`
5. 在 section 循环后插入第3～5部分预留区块

---

### 2.7 Parser 修正

1. `_parse_implementation_summary`：
   - 过滤 `Unnamed`、空列名（`drop_unnamed_columns`）
   - 按 `column_mapping` 将 Excel 列映射到 `output_columns`
   - 对 `date_columns` 做 Excel 序列号 → `YYYY-MM-DD` 转换
   - 无序号列时按 `auto_sequence` 自动生成
2. 输出 `columns` 严格为 `["序号","任务","开始时间","结束时间","实施人","复核人"]`（或配置的 output_columns）

---

### 2.8 日期转换算法

```python
# Excel 日期序列号：1900-01-01 为 1，46315 约为 2026-10-xx
def excel_serial_to_date(val) -> str:
    if isinstance(val, (int, float)) and val > 0 and val < 2958466:
        from datetime import datetime, timedelta
        base = datetime(1899, 12, 30)  # Excel 基准
        d = base + timedelta(days=int(val))
        return d.strftime("%Y-%m-%d")
    return str(val) if val is not None else ""
```

---

## 3. 实现任务拆解（供 Developer）

| 序号 | 任务 | 模块 | 产出 |
|------|------|------|------|
| 1 | rules.yaml 增加 implementation_summary.column_mapping、date_columns、output_columns、drop_unnamed_columns、auto_sequence | config | 配置更新 |
| 2 | Parser：过滤 Unnamed 列、列映射、日期转换、序号自动生成 | src/parser | excel_parser.py |
| 3 | create_template.py：第1部分、第3～5部分、第2部分结构调整、实施总表 6 列、2.1.x 编号 | scripts | create_template.py |
| 4 | template.docx：执行 create_template 重新生成 | templates | template.docx |
| 5 | 单元测试 / 端到端测试适配 | tests | 测试用例 |

---

## 4. 架构决策日志（补充）

| 决策 | 理由 |
|------|------|
| 实施总表固定 6 列 | 与样例「序号\|任务\|开始时间\|结束时间\|实施人\|复核人」一致，避免列错乱 |
| 日期列做 Excel 序列号转换 | 46315 等为 Excel 内部表示，必须转为可读格式 |
| 过滤 Unnamed 列 | pandas 对空/重复表头会生成 Unnamed，不应输出 |
| 第1/3～5部分使用占位 | PRD 称「预留标准模版」，可先占位后迭代 |
| 2.1.x 编号由模板 loop.index 生成 | 动态 section 数量，编号随循环递增 |

---

## 5. 风险与依赖

| 风险 | 缓解 |
|------|------|
| 样例 Excel 列名与配置不一致 | column_mapping 支持多别名，可扩展 |
| 日期列含非序列号值 | 转换前校验类型，非数字则原样输出 |
| 第1部分内容来源 | 本期可占位；后续可从 meta 或独立配置扩展 |
