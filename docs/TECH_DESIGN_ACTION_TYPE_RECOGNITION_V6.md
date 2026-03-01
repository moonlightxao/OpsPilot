# 技术方案：Excel 导入自动识别操作类型 (V6)

**版本**: v1.0
**日期**: 2026-03-01
**作者**: Architect
**状态**: 待 Developer 实现

---

## 1. 需求概述

### 1.1 功能描述

在导入 Excel 后，系统自动识别每个 Sheet 中「操作类型」列的去重值，并保存到 `action_library` 中。

### 1.2 核心规则

| 项目 | 说明 |
|------|------|
| **识别方式** | 读取每个 Sheet 的「操作类型」列（通过 `core_fields.action_type.aliases` 匹配列名） |
| **保存位置** | 按 Sheet 名分类保存到 `action_library.{Sheet名}.{操作类型名}` |
| **默认属性** | `{instruction: 操作类型名, is_high_risk: false, render_table: true}` |
| **同名冲突** | 预览界面显示冲突标记，用户确认覆盖/跳过 |
| **无操作类型列** | 跳过该 Sheet |

---

## 2. 技术方案

### 2.1 改动点概览

| 改动类型 | 文件 | 说明 |
|----------|------|------|
| 修改 | `src/web/routes/upload.py` | 预览 API 返回识别到的操作类型 |
| 新增 | `src/web/services/config_service.py` | 新增 `batch_save_action_types` 方法 |
| 修改 | `src/web/routes/config.py` | 新增操作类型批量保存 API |
| 修改 | `src/web/templates/partials/columns.html` | 预览界面展示操作类型列表 |

### 2.2 API 设计

#### 2.2.1 修改预览 API

**接口**: `POST /api/upload/excel/preview`

**当前返回**:
```json
{
  "success": true,
  "sheets": [{"name": "Sheet1", "columns": [...], "is_first_sheet": true}],
  "current_priority_rules": ["Sheet2"],
  "max_priority": 20
}
```

**新增返回字段**:
```json
{
  "success": true,
  "sheets": [...],
  "current_priority_rules": [...],
  "max_priority": 20,
  "recognized_action_types": {
    "ROMA任务": {
      "column_name": "操作",
      "action_types": ["新增", "删除", "修改"]
    },
    "应用配置": {
      "column_name": "操作类型",
      "action_types": ["新增", "修改"]
    }
  },
  "existing_action_types": {
    "ROMA任务": ["新增", "删除"],
    "应用配置": ["新增"]
  }
}
```

**字段说明**:
- `recognized_action_types`: 识别到的操作类型（按 Sheet 分组）
  - `column_name`: 匹配到的列名
  - `action_types`: 去重后的操作类型值列表
- `existing_action_types`: 已存在的操作类型（用于前端判断冲突）

#### 2.2.2 新增操作类型批量保存 API

**接口**: `POST /api/config/action-types/batch-save`

**请求体**:
```json
{
  "action_types": {
    "ROMA任务": {
      "新增": {"overwrite": false},
      "删除": {"overwrite": true},
      "修改": {"overwrite": false}
    },
    "应用配置": {
      "新增": {"overwrite": true},
      "修改": {"overwrite": false}
    }
  }
}
```

**返回**:
```json
{
  "success": true,
  "message": "已保存 5 个操作类型，跳过 1 个已存在项",
  "saved": {
    "ROMA任务": ["新增", "修改"],
    "应用配置": ["修改"]
  },
  "skipped": {
    "ROMA任务": ["删除"]
  }
}
```

### 2.3 ConfigService 扩展

新增方法：

```python
def batch_save_action_types(self, action_types: dict) -> dict:
    """
    批量保存操作类型

    Args:
        action_types: {
            "Sheet名": {
                "操作类型名": {"overwrite": true/false},
                ...
            },
            ...
        }

    Returns:
        {
            "saved": {"Sheet名": ["操作类型名", ...]},
            "skipped": {"Sheet名": ["操作类型名", ...]}
        }
    """
```

### 2.4 操作类型列识别逻辑

```python
def _find_action_type_column(self, columns: list) -> Optional[str]:
    """
    在列名列表中查找操作类型列

    匹配规则：
    1. 获取 core_fields.action_type.aliases
    2. 遍历列名，检查是否包含任一别名（不区分大小写，部分匹配）
    3. 返回第一个匹配的列名，无匹配返回 None
    """
    config = self.load()
    aliases = config.get("core_fields", {}).get("action_type", {}).get("aliases", [])

    for col in columns:
        col_str = str(col).lower()
        for alias in aliases:
            if alias.lower() in col_str:
                return str(col)
    return None
```

### 2.5 前端改动

#### 预览界面新增操作类型展示

在 Sheet 卡片下方新增操作类型列表区域：

```html
<!-- 操作类型识别结果 -->
<div class="action-types-section" v-if="sheet.recognizedActionTypes">
  <div class="section-title">识别到的操作类型</div>
  <div class="action-type-list">
    <div v-for="action in sheet.recognizedActionTypes" class="action-type-item">
      <label>
        <input type="checkbox" :checked="!action.exists" :disabled="!action.exists" v-model="action.selected">
        <span>{{ action.name }}</span>
        <span v-if="action.exists" class="conflict-badge">⚠️ 已存在</span>
        <span v-if="action.exists" class="overwrite-label">
          <input type="checkbox" v-model="action.overwrite"> 覆盖
        </span>
      </label>
    </div>
  </div>
</div>
```

---

## 3. 开发任务拆解

### 3.1 后端任务

| 任务ID | 描述 | 优先级 |
|--------|------|--------|
| V6-B1 | 修改预览 API：读取数据行，识别操作类型列，返回去重值 | P0 |
| V6-B2 | ConfigService 扩展：新增 `_find_action_type_column` 方法 | P0 |
| V6-B3 | ConfigService 扩展：新增 `batch_save_action_types` 方法 | P0 |
| V6-B4 | API 路由：新增 `POST /api/config/action-types/batch-save` | P0 |

### 3.2 前端任务

| 任务ID | 描述 |
|--------|------|
| V6-F1 | 预览界面：展示识别到的操作类型列表 |
| V6-F2 | 冲突处理：已存在项显示标记和覆盖勾选框 |
| V6-F3 | 保存交互：收集用户确认后调用批量保存 API |

### 3.3 测试任务

| 任务ID | 描述 |
|--------|------|
| V6-T1 | 单元测试：操作类型列识别逻辑 |
| V6-T2 | 单元测试：批量保存 API（新增、覆盖、跳过场景） |
| V6-T3 | 单元测试：无操作类型列的 Sheet 跳过处理 |

---

## 4. 数据结构

### 4.1 预览 API 响应结构

```typescript
interface PreviewResponse {
  success: boolean;
  sheets: SheetInfo[];
  current_priority_rules: string[];
  max_priority: number;
  recognized_action_types: Record<string, RecognizedActions>;
  existing_action_types: Record<string, string[]>;
}

interface RecognizedActions {
  column_name: string;
  action_types: string[];
}

interface SheetInfo {
  name: string;
  columns: string[];
  is_first_sheet: boolean;
}
```

### 4.2 批量保存请求结构

```typescript
interface BatchSaveRequest {
  action_types: Record<string, Record<string, { overwrite: boolean }>>;
}
```

---

## 5. 验收标准

1. 上传包含「操作类型」列的 Excel，系统能正确识别所有去重值
2. 新操作类型自动保存到对应 Sheet 章节，默认属性正确填充
3. 已存在的操作类型显示冲突标记，需用户确认覆盖
4. 用户选择「跳过」的操作类型不被覆盖
5. 无「操作类型」列的 Sheet 不处理
6. 多个 Sheet 有同名操作类型时，各自独立保存

---

## 6. 风险评估

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| Excel 数据量大导致预览慢 | 中 | 仅读取前 1000 行数据用于识别 |
| 操作类型值包含特殊字符 | 低 | 保存前进行字符串清洗 |

---

## 7. 产出物清单

| 文件 | 改动类型 |
|------|----------|
| `src/web/routes/upload.py` | 修改 |
| `src/web/routes/config.py` | 修改 |
| `src/web/services/config_service.py` | 修改 |
| `src/web/templates/partials/columns.html` | 修改 |
| `tests/test_action_type_recognition_v6.py` | 新增 |
