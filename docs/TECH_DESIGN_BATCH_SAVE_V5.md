# 技术方案：Excel 一键保存全量覆盖模式 (V5)

**版本**: v1.0
**日期**: 2026-03-01
**作者**: Architect
**状态**: 待 Developer 实现

---

## 1. 需求概述

### 1.1 问题背景

用户反馈：Excel 一键保存后，配置文件出现累积/膨胀问题。
- 当前实现采用**增量更新**模式
- 历史配置无法自动清理
- `rules.yaml` 中存在测试数据、废弃字段

### 1.2 期望行为

| 配置项 | 当前行为 | 期望行为 |
|--------|----------|----------|
| `sheet_column_mapping` | 增量更新 | **全量覆盖**（删除 Excel 中不存在的 Sheet） |
| `priority_rules` | 增量添加（仅新增） | **全量覆盖**（删除 Excel 中不存在的章节） |
| `action_library` | 不修改 | **保留**（不删除现有配置） |
| `core_fields` | 增量添加别名 | **全量重新生成**（删除不存在的字段） |

---

## 2. 技术方案

### 2.1 核心改动点

修改 `src/web/services/config_service.py` 中的两个方法：

1. **`batch_save_sheets`**：改为全量覆盖模式
2. **`sync_core_fields_from_columns`**：改为全量重新生成模式

### 2.2 `batch_save_sheets` 方法重构

**当前逻辑**（增量更新）:
```python
# 当前：读取配置 → 增量更新 → 保存
config = self.load()
config["sheet_column_mapping"][name] = {...}  # 增量添加
if name not in priority_rules:  # 仅新增
    config["priority_rules"][name] = priority
self.save(config)
```

**新逻辑**（全量覆盖）:
```python
# 新逻辑：完全基于 Excel 重新生成
config["sheet_column_mapping"] = {}  # 清空后重建
config["priority_rules"] = {}  # 清空后重建（跳过第一个 Sheet）

for sheet in sheets:
    config["sheet_column_mapping"][name] = {...}
    if not is_first:
        config["priority_rules"][name] = priority  # 按顺序分配

# 不触碰 action_library
self.save(config)
```

**具体改动**:

1. 删除「读取现有配置」中 `sheet_column_mapping` 和 `priority_rules` 的保留逻辑
2. 直接基于 Excel 内容重新生成这两个配置项
3. 优先级按 Sheet 顺序自动分配（10, 20, 30...），不再使用「当前最大值 + 10」
4. 调用 `sync_core_fields_from_columns` 进行全量同步

### 2.3 `sync_core_fields_from_columns` 方法重构

**当前逻辑**（增量添加）:
```python
# 当前：保留现有 core_fields，仅添加新别名
core_fields = config.get("core_fields", {})
for column in all_columns:
    if column not in current_aliases:
        current_aliases.add(column)  # 增量添加
```

**新逻辑**（全量重新生成）:
```python
# 新逻辑：完全基于新列名重新生成
new_core_fields = {}

# 1. 保留预置核心字段的基本配置（required 属性）
for field_name in PREDEFINED_FIELDS:
    new_core_fields[field_name] = {
        "aliases": [],  # 清空，后续根据列名重新填充
        "required": PREDEFINED_FIELDS[field_name]["required"]
    }

# 2. 根据列名重新填充 aliases
for column in all_columns:
    matched_field = match_core_field(column)
    if matched_field:
        new_core_fields[matched_field]["aliases"].append(column)
    else:
        # 创建自定义字段
        new_core_fields[column] = {"aliases": [column], "required": False, "custom": True}

config["core_fields"] = new_core_fields
```

**具体改动**:

1. 不再保留现有 `core_fields`，而是完全重新生成
2. 保留预置核心字段的 `required` 属性（action_type: true, 其他: false）
3. 删除不存在的自定义字段
4. 别名完全基于当前列名重新生成

---

## 3. 开发任务拆解

### 3.1 后端任务

| 任务ID | 描述 | 优先级 |
|--------|------|--------|
| V5-B1 | 重构 `batch_save_sheets` 方法：全量覆盖 `sheet_column_mapping` | P0 |
| V5-B2 | 重构 `batch_save_sheets` 方法:全量覆盖 `priority_rules`，按顺序分配优先级 | P0 |
| V5-B3 | 重构 `sync_core_fields_from_columns` 方法:全量重新生成 `core_fields` | P0 |
| V5-B4 | 更新 API 返回值：增加 `deleted` 字段记录被删除的配置项 | P1 |

### 3.2 测试任务

| 任务ID | 描述 |
|--------|------|
| V5-T1 | 单元测试：上传包含 Sheet A、B、C 的 Excel，验证 `sheet_column_mapping` 仅包含 A、B、C |
| V5-T2 | 单元测试：原有配置包含 Sheet D、E，上传 Excel 后验证 D、E 被删除 |
| V5-T3 | 单元测试：验证 `action_library` 保持不变 |
| V5-T4 | 单元测试：验证 `priority_rules` 按 Sheet 顺序分配（10, 20, 30...） |
| V5-T5 | 单元测试：验证 `core_fields` 基于新列名重新生成，旧字段被清理 |

---

## 4. 接口变更

### 4.1 `POST /api/config/batch-save` 返回值扩展

**当前返回**:
```json
{
  "success": true,
  "message": "配置已保存",
  "updated": {
    "sheet_column_mapping": ["Sheet1", "Sheet2"],
    "priority_rules": ["Sheet2"]
  }
}
```

**新返回**:
```json
{
  "success": true,
  "message": "配置已保存",
  "updated": {
    "sheet_column_mapping": ["Sheet1", "Sheet2"],
    "priority_rules": ["Sheet2"]
  },
  "deleted": {
    "sheet_column_mapping": ["OldSheet1"],
    "priority_rules": ["OldSheet2"],
    "core_fields": ["旧字段1", "旧字段2"]
  }
}
```

---

## 5. 风险评估

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| 用户误操作导致配置丢失 | 高 | 保存前自动备份（已有 BackupService） |
| 首次使用不理解行为变化 | 中 | Toast 提示中说明「已清理 N 个废弃配置」 |

---

## 6. 验收标准

1. 上传包含 Sheet A、B、C 的 Excel 并保存后：
   - `sheet_column_mapping` **仅包含** A、B、C
   - `priority_rules` **仅包含** B、C（跳过第一个 Sheet A）
   - 优先级为 B:10, C:20

2. 原有配置包含 Sheet D、E，上传 Excel（不含 D、E）后：
   - D、E 从 `sheet_column_mapping` 中**被删除**
   - D、E 从 `priority_rules` 中**被删除**

3. `action_library` **保持不变**（不删除任何操作类型配置）

4. `core_fields` 基于新列名重新生成：
   - 预置字段的 `required` 属性保持不变
   - 不存在的自定义字段**被删除**

---

## 7. 产出物清单

| 文件 | 改动类型 |
|------|----------|
| `src/web/services/config_service.py` | 修改 |
| `tests/test_web_api_v5.py` | 新增 |

---

## 8. 下一步

**待 Developer 实现**：
1. 完成 V5-B1 ~ V5-B4 开发任务
2. 完成 V5-T1 ~ V5-T5 测试任务
3. 验证验收标准全部通过
