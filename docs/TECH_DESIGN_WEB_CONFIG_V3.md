# Web 配置中心技术方案 v3.0

## 1. 需求概述

**来源**: `docs/OpsPilot_PRD.md` 3.4.3-C 节「核心字段同步」

**需求背景**:
- 用户在列映射页面上传 Excel 后，手动删除不需要的列
- 但 `core_fields` 中的别名未同步更新，仍包含已删除的列名
- 解析器使用 `core_fields` 匹配 Excel 列名，导致解析异常

**解决方案**: 在列映射页面增加「同步到核心字段」按钮，用户手动触发同步

**核心约束**:
- 用户手动触发，而非自动同步（避免误操作）
- 仅更新 `aliases`，保持 `required` 属性不变
- 遵循关键词匹配规则，不随意覆盖

---

## 2. 数据结构分析

### 2.1 当前 core_fields 结构

```yaml
core_fields:
  action_type:
    aliases:
      - 操作类型
      - 操作
      - Action
    required: true
  deploy_unit:
    aliases:
      - 部署单元
      - 应用名
      - 服务名
    required: false
  executor:
    aliases:
      - 执行人
      - 实施人
      - 负责人
    required: false
  external_link:
    aliases:
      - 外部链接
      - 链接
      - URL
    required: false
  task_name:
    aliases:
      - 任务名
      - 任务名称
      - Task Name
    required: true
```

### 2.2 sheet_column_mapping 结构

```yaml
sheet_column_mapping:
  应用配置:
    columns:
      - 操作类型
      - 部署单元
      - 键
      - 值
      - 实施人
      - 复核人
    column_mapping:
      操作类型: [操作类型]
      部署单元: [部署单元]
      ...
  容器配置:
    columns:
      - 操作类型
      - 部署单元
      - 参数
      - 值
      - 实施人
      - 复核人
    ...
```

### 2.3 同步规则

| 核心字段 | 关键词匹配规则 | 示例列名 |
|----------|----------------|----------|
| `action_type` | 包含 "操作类型"、"操作"、"Action" | 操作类型、操作、Action Type |
| `deploy_unit` | 包含 "部署单元"、"应用名"、"服务名"、"应用名称" | 部署单元、应用名、服务名 |
| `executor` | 包含 "执行人"、"实施人"、"负责人"、"复核人" | 执行人、实施人、复核人 |
| `task_name` | 包含 "任务名"、"任务名称"、"Task" | 任务名、任务名称、Task Name |
| `external_link` | 包含 "外部链接"、"链接"、"URL" | 外部链接、链接、URL |

**同步行为**:
- **增量更新**：仅添加匹配的新列名，不删除现有别名
- **去重**：确保 aliases 中无重复项
- **保持 required**：预置字段的 `required` 属性保持不变

---

## 3. 技术实现

### 3.1 ConfigService 扩展

```python
# src/web/services/config_service.py 新增方法

# 核心字段关键词映射
CORE_FIELD_KEYWORDS = {
    "action_type": ["操作类型", "操作", "action"],
    "deploy_unit": ["部署单元", "应用名", "服务名", "应用名称"],
    "executor": ["执行人", "实施人", "负责人", "复核人"],
    "task_name": ["任务名", "任务名称", "task"],
    "external_link": ["外部链接", "链接", "url"]
}

def sync_core_fields_from_columns(self) -> dict:
    """
    从 sheet_column_mapping 同步列名到 core_fields

    同步规则：
    1. 遍历所有 Sheet 的 columns，收集去重后的列名列表
    2. 根据关键词匹配规则，将列名添加到对应核心字段的 aliases
    3. 增量更新：仅添加新列名，不删除现有别名
    4. 保持 required 属性不变

    Returns:
        同步结果 {
            "synced_count": 同步的核心字段数量,
            "updated_fields": 更新的字段列表,
            "new_aliases": {字段名: [新增别名列表]}
        }
    """
    config = self.load()

    # 1. 收集所有列名并去重
    all_columns = set()
    sheet_column_mapping = config.get("sheet_column_mapping", {})
    for sheet_name, sheet_config in sheet_column_mapping.items():
        columns = sheet_config.get("columns", [])
        all_columns.update(columns)

    # 2. 初始化 core_fields（如果不存在）
    if "core_fields" not in config:
        config["core_fields"] = self._get_default_core_fields()

    core_fields = config["core_fields"]

    # 3. 遍历列名，根据关键词匹配到核心字段
    result = {
        "synced_count": 0,
        "updated_fields": [],
        "new_aliases": {}
    }

    for column in all_columns:
        matched_field = self._match_core_field(column)
        if matched_field and matched_field in core_fields:
            # 获取当前 aliases
            current_aliases = set(core_fields[matched_field].get("aliases", []))

            # 如果列名不在 aliases 中，添加
            if column not in current_aliases:
                current_aliases.add(column)
                core_fields[matched_field]["aliases"] = list(current_aliases)

                # 记录结果
                if matched_field not in result["new_aliases"]:
                    result["new_aliases"][matched_field] = []
                result["new_aliases"][matched_field].append(column)

                if matched_field not in result["updated_fields"]:
                    result["updated_fields"].append(matched_field)

    # 4. 保存配置
    if result["updated_fields"]:
        config["core_fields"] = core_fields
        self.save(config)
        result["synced_count"] = len(result["updated_fields"])

    return result

def _match_core_field(self, column_name: str) -> Optional[str]:
    """
    根据列名匹配核心字段

    Args:
        column_name: 列名

    Returns:
        匹配的核心字段名，无匹配返回 None
    """
    column_lower = column_name.lower()

    for field_name, keywords in CORE_FIELD_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in column_lower:
                return field_name

    return None

def _get_default_core_fields(self) -> dict:
    """获取默认的核心字段配置"""
    return {
        "action_type": {
            "aliases": ["操作类型", "操作", "Action"],
            "required": True
        },
        "deploy_unit": {
            "aliases": ["部署单元", "应用名", "服务名"],
            "required": False
        },
        "executor": {
            "aliases": ["执行人", "实施人", "负责人"],
            "required": False
        },
        "external_link": {
            "aliases": ["外部链接", "链接", "URL"],
            "required": False
        },
        "task_name": {
            "aliases": ["任务名", "任务名称"],
            "required": True
        }
    }
```

### 3.2 API 路由

```python
# src/web/routes/config.py 新增

@config_bp.route('/sync-core-fields', methods=['POST'])
def sync_core_fields():
    """
    同步核心字段

    从 sheet_column_mapping 中收集所有列名，
    根据关键词匹配规则更新 core_fields 的 aliases
    """
    try:
        result = config_service.sync_core_fields_from_columns()

        if result["synced_count"] > 0:
            return jsonify({
                "success": True,
                "message": f"已同步 {result['synced_count']} 个核心字段",
                "data": result
            })
        else:
            return jsonify({
                "success": True,
                "message": "无需同步，所有列名已存在于核心字段中",
                "data": result
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
```

### 3.3 前端实现

#### 3.3.1 列映射页面增加按钮

```html
<!-- src/web/templates/partials/columns.html 底部工具栏 -->

<div class="toolbar-actions">
    <!-- 现有按钮 -->
    <button id="upload-excel-btn" class="btn btn-secondary">
        <i class="icon-upload"></i> 上传 Excel 识别
    </button>

    <!-- 新增：同步到核心字段按钮 -->
    <button id="sync-core-fields-btn" class="btn btn-primary">
        <i class="icon-sync"></i> 同步到核心字段
    </button>
</div>
```

#### 3.3.2 JavaScript 交互

```javascript
// 同步到核心字段
document.getElementById('sync-core-fields-btn').addEventListener('click', async function() {
    const btn = this;
    btn.disabled = true;
    btn.textContent = '同步中...';

    try {
        const response = await fetch('/api/config/sync-core-fields', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();

        if (result.success) {
            showToast(result.message, 'success');

            // 如果有新增别名，显示详情
            if (result.data && result.data.new_aliases) {
                const details = Object.entries(result.data.new_aliases)
                    .map(([field, aliases]) => `${field}: ${aliases.join(', ')}`)
                    .join('\n');
                console.log('新增别名:\n' + details);
            }
        } else {
            showToast(result.error || '同步失败', 'error');
        }
    } catch (error) {
        showToast('同步失败: ' + error.message, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="icon-sync"></i> 同步到核心字段';
    }
});
```

---

## 4. 开发任务拆解

### 4.1 后端任务 (Owner: Developer)

| 任务编号 | 任务描述 | 预估工时 |
|----------|----------|----------|
| **CF-B1** | ConfigService 扩展：新增 `sync_core_fields_from_columns` 方法 | 1h |
| **CF-B2** | ConfigService 扩展：新增 `_match_core_field` 关键词匹配方法 | 0.5h |
| **CF-B3** | API 路由：核心字段同步 API（POST `/api/config/sync-core-fields`） | 0.5h |

### 4.2 前端任务 (Owner: Developer)

| 任务编号 | 任务描述 | 预估工时 |
|----------|----------|----------|
| **CF-F1** | 列映射页面：底部工具栏增加「同步到核心字段」按钮 | 0.5h |
| **CF-F2** | 同步交互：点击按钮调用 API，显示 Toast 提示同步结果 | 0.5h |

### 4.3 测试任务 (Owner: Tester)

| 任务编号 | 任务描述 | 预估工时 |
|----------|----------|----------|
| **CF-T1** | API 单元测试：核心字段同步 API | 0.5h |
| **CF-T2** | 关键词匹配测试：验证各种列名匹配规则 | 0.5h |
| **CF-T3** | E2E 测试：同步按钮交互流程 | 0.5h |

---

## 5. 验收标准

| 验收项 | 通过标准 |
|--------|----------|
| 按钮位置 | 列映射页面底部工具栏有「同步到核心字段」按钮 |
| 同步触发 | 点击按钮后，API 被正确调用 |
| 列名收集 | 遍历所有 Sheet 的 columns，正确收集列名 |
| 关键词匹配 | 列名能根据关键词规则匹配到正确的核心字段 |
| 增量更新 | 仅添加新列名，不删除现有 aliases |
| 保持属性 | required 属性保持不变 |
| Toast 提示 | 同步成功后显示"已同步 N 个核心字段" |
| 解析器验证 | 同步后，解析器使用更新后的 core_fields 能正确匹配 Excel 列名 |

---

## 6. 测试用例示例

### 6.1 关键词匹配测试

```python
def test_match_core_field():
    """测试关键词匹配规则"""
    service = ConfigService()

    # action_type 匹配
    assert service._match_core_field("操作类型") == "action_type"
    assert service._match_core_field("操作") == "action_type"
    assert service._match_core_field("Action") == "action_type"
    assert service._match_core_field("Action Type") == "action_type"

    # deploy_unit 匹配
    assert service._match_core_field("部署单元") == "deploy_unit"
    assert service._match_core_field("应用名") == "deploy_unit"
    assert service._match_core_field("服务名") == "deploy_unit"

    # executor 匹配
    assert service._match_core_field("执行人") == "executor"
    assert service._match_core_field("实施人") == "executor"
    assert service._match_core_field("复核人") == "executor"

    # task_name 匹配
    assert service._match_core_field("任务名") == "task_name"
    assert service._match_core_field("任务名称") == "task_name"
    assert service._match_core_field("Task Name") == "task_name"

    # 无匹配
    assert service._match_core_field("备注") is None
    assert service._match_core_field("其他列") is None
```

### 6.2 同步 API 测试

```python
def test_sync_core_fields_api(client):
    """测试核心字段同步 API"""
    # 准备测试数据
    # sheet_column_mapping 中有 "任务序号" 列
    # core_fields.task_name.aliases 不包含 "任务序号"

    response = client.post('/api/config/sync-core-fields')
    data = response.get_json()

    assert data["success"] is True
    assert "task_name" in data["data"]["updated_fields"]
    assert "任务序号" in data["data"]["new_aliases"]["task_name"]
```

---

## 7. 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 关键词误匹配 | 低 | 使用严格的关键词规则，测试覆盖各种边界情况 |
| 重复同步 | 无 | 增量更新，已存在的列名不会重复添加 |
| 性能问题 | 低 | 单人使用场景，数据量有限 |

---

**文档版本**: v3.0
**创建日期**: 2026-02-26
**创建者**: Architect
**更新说明**: 新增核心字段同步功能技术方案
**前置文档**: `docs/TECH_DESIGN_WEB_CONFIG_V2.md`
