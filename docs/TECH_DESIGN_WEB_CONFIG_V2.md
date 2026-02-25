# Web 配置中心技术方案 v2.0

## 1. 需求概述

**来源**: `docs/OpsPilot_PRD.md` 3.4.3-A/B/C 节更新

**新增功能**:
1. **操作类型与章节绑定** - 每个章节拥有独立的操作类型配置库
2. **批量删除功能** - 章节排序、操作类型、列映射页面支持多选批量删除

**核心约束**:
- 保持与现有架构的兼容性
- 遵循简洁原则，最小化代码改动
- 数据迁移向后兼容

---

## 2. 功能一：操作类型与章节绑定

### 2.1 需求分析

**当前结构**（扁平）:
```yaml
action_library:
  "新增":
    instruction: "..."
    is_high_risk: false
  "删除":
    instruction: "..."
    is_high_risk: true
```

**目标结构**（章节嵌套）:
```yaml
action_library:
  "应用配置":           # 章节名作为 Key
    "新增":             # 操作类型
      instruction: "登录配置中心，进入应用配置页面..."
      is_high_risk: false
      render_table: true
    "删除":
      instruction: "确认影响范围后，执行删除操作..."
      is_high_risk: true
      render_table: true
  "容器配置":
    "扩容":
      instruction: "进入容器管理平台..."
      is_high_risk: false
      render_table: true
```

### 2.2 数据迁移策略

**兼容性原则**: 读取时自动兼容旧格式，保存时统一使用新格式。

```python
def get_action_library(self) -> Dict[str, Any]:
    """获取操作类型配置，自动兼容新旧格式"""
    raw_library = self.get('action_library', {})

    # 检测是否为旧格式（扁平结构）
    if self._is_flat_format(raw_library):
        # 自动迁移到新格式（归入"默认"章节）
        return {"默认": raw_library}

    return raw_library

def _is_flat_format(self, library: Dict) -> bool:
    """检测是否为旧格式"""
    if not library:
        return False
    # 旧格式: 顶层键的值包含 instruction/is_high_risk
    first_value = next(iter(library.values()), {})
    return isinstance(first_value, dict) and 'instruction' in first_value
```

### 2.3 API 扩展

#### 2.3.1 新增 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/config/action-library/<chapter>` | GET | 获取指定章节的操作类型列表 |
| `/api/config/action-library/<chapter>` | PUT | 设置指定章节的操作类型配置 |
| `/api/config/action-library/<chapter>/<action_name>` | PUT | 设置指定章节的某个操作类型 |
| `/api/config/action-library/<chapter>/<action_name>` | DELETE | 删除指定章节的某个操作类型 |
| `/api/config/action-library/batch-delete` | POST | 批量删除操作类型 |
| `/api/config/priority-rules/batch-delete` | POST | 批量删除章节 |
| `/api/config/sheet-column-mapping/batch-delete` | POST | 批量删除列映射 |

#### 2.3.2 请求/响应示例

```python
# GET /api/config/action-library/应用配置
{
    "success": true,
    "data": {
        "新增": {
            "instruction": "登录配置中心...",
            "is_high_risk": false,
            "render_table": true
        },
        "删除": {
            "instruction": "确认影响范围...",
            "is_high_risk": true,
            "render_table": true
        }
    }
}

# POST /api/config/action-library/batch-delete
# 请求:
{
    "chapter": "应用配置",
    "action_names": ["新增", "修改"]
}
# 响应:
{
    "success": true,
    "message": "已删除 2 个操作类型",
    "deleted": ["新增", "修改"]
}
```

### 2.4 ConfigService 扩展

```python
# 新增方法

def get_chapter_actions(self, chapter: str) -> Dict[str, Dict[str, Any]]:
    """获取指定章节的操作类型配置"""
    library = self.get_action_library()
    return library.get(chapter, {})

def set_chapter_actions(self, chapter: str, actions: Dict[str, Any]) -> None:
    """设置指定章节的操作类型配置"""
    library = self.get_action_library()
    library[chapter] = actions
    self.set_action_library(library)

def set_chapter_action(self, chapter: str, action_name: str, config: Dict[str, Any]) -> None:
    """设置指定章节的某个操作类型"""
    library = self.get_action_library()
    if chapter not in library:
        library[chapter] = {}
    library[chapter][action_name] = config
    self.set_action_library(library)

def delete_chapter_action(self, chapter: str, action_name: str) -> bool:
    """删除指定章节的某个操作类型"""
    library = self.get_action_library()
    if chapter in library and action_name in library[chapter]:
        del library[chapter][action_name]
        self.set_action_library(library)
        return True
    return False

def batch_delete_chapter_actions(self, chapter: str, action_names: list) -> list:
    """批量删除指定章节的操作类型"""
    library = self.get_action_library()
    deleted = []
    if chapter in library:
        for name in action_names:
            if name in library[chapter]:
                del library[chapter][name]
                deleted.append(name)
        if deleted:
            self.set_action_library(library)
    return deleted

def batch_delete_chapters(self, sheet_names: list) -> list:
    """批量删除章节"""
    priority_rules = self.get_priority_rules()
    deleted = []
    for name in sheet_names:
        if name in priority_rules:
            del priority_rules[name]
            deleted.append(name)
    if deleted:
        self.set_priority_rules(priority_rules)
    return deleted

def batch_delete_sheet_mappings(self, sheet_names: list) -> list:
    """批量删除 Sheet 列映射"""
    mapping = self.get_sheet_column_mapping()
    deleted = []
    for name in sheet_names:
        if name in mapping:
            del mapping[name]
            deleted.append(name)
    if deleted:
        self.set_sheet_column_mapping(mapping)
    return deleted
```

### 2.5 前端页面重构

#### 2.5.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│  操作类型配置                                          [+ 新增操作类型]    │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌─────────────────────────────────────────────┐  │
│  │  章节列表         │  │  当前章节：应用配置                          │  │
│  │  ─────────────   │  │  ─────────────────────────────────────────  │  │
│  │  □ 应用配置 ✓    │  │  □ 新增    [操作说明...]    [编辑] [删除]    │  │
│  │  □ 容器配置      │  │  □ 修改    [操作说明...]    [编辑] [删除]    │  │
│  │  □ MQS配置       │  │  ☑ 删除    [高危操作!]      [编辑] [删除]    │  │
│  │  □ ROMA任务      │  │                                             │  │
│  │                  │  │  ─────────────────────────────────────────  │  │
│  │  [新增章节]       │  │  [批量删除]  已选择 1 项                     │  │
│  └──────────────────┘  └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 2.5.2 交互规范

| 操作 | 交互方式 |
|------|----------|
| 切换章节 | 点击左侧章节列表，右侧显示该章节的操作类型 |
| 新增操作类型 | 点击"新增操作类型"按钮，弹出编辑弹窗 |
| 编辑操作类型 | 点击"编辑"按钮，弹出编辑弹窗（预填当前值） |
| 删除操作类型 | 点击"删除"按钮，二次确认后删除 |
| 批量删除 | 勾选多个操作类型，点击"批量删除"，二次确认后删除 |
| 新增章节 | 在章节列表底部点击"新增章节" |

---

## 3. 功能二：批量删除功能

### 3.1 适用范围

| 页面 | 批量删除对象 | 新增 API |
|------|--------------|----------|
| 章节排序配置 | 章节项 | `POST /api/config/priority-rules/batch-delete` |
| 操作类型配置 | 操作类型项 | `POST /api/config/action-library/batch-delete` |
| 列映射配置 | Sheet 项 | `POST /api/config/sheet-column-mapping/batch-delete` |

### 3.2 统一交互模式

```
┌─────────────────────────────────────────────────────────────────────────┐
│  章节排序配置                                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  ☑ 应用配置      优先级: 10    [编辑] [删除]                             │
│  □ 容器配置      优先级: 20    [编辑] [删除]                             │
│  ☑ MQS配置       优先级: 30    [编辑] [删除]                             │
│  □ ROMA任务      优先级: 40    [编辑] [删除]                             │
├─────────────────────────────────────────────────────────────────────────┤
│  [批量删除]  已选择 2 项                               [+ 新增章节]       │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.3 前端组件设计

#### 3.3.1 批量选择状态管理

```javascript
// 通用批量选择状态管理
const batchSelect = {
    selected: new Set(),

    toggle(itemKey) {
        if (this.selected.has(itemKey)) {
            this.selected.delete(itemKey);
        } else {
            this.selected.add(itemKey);
        }
        this.updateUI();
    },

    selectAll(items) {
        items.forEach(item => this.selected.add(item.key));
        this.updateUI();
    },

    clearAll() {
        this.selected.clear();
        this.updateUI();
    },

    updateUI() {
        const count = this.selected.size;
        const btn = document.getElementById('batch-delete-btn');
        const counter = document.getElementById('selected-count');

        if (counter) counter.textContent = count;
        if (btn) btn.disabled = count === 0;
    },

    getSelected() {
        return Array.from(this.selected);
    }
};
```

#### 3.3.2 批量删除确认弹窗

```javascript
async function batchDelete(type, items) {
    const count = items.length;
    const message = `确定要删除选中的 ${count} 个${type}吗？此操作不可撤销。`;

    showConfirm('批量删除确认', message, async () => {
        const endpoint = getBatchDeleteEndpoint(type);
        const body = getBatchDeleteBody(type, items);

        try {
            const res = await apiRequest(endpoint, 'POST', body);
            if (res.success) {
                showToast(`已删除 ${res.deleted.length} 个${type}`, 'success');
                batchSelect.clearAll();
                reloadCurrentPage();
            } else {
                showToast(res.error || '删除失败', 'error');
            }
        } catch (err) {
            showToast('删除失败', 'error');
        }
    });
}
```

### 3.4 API 实现

#### 3.4.1 章节批量删除

```python
@config_bp.route('/priority-rules/batch-delete', methods=['POST'])
def batch_delete_chapters():
    """批量删除章节"""
    try:
        data = request.get_json()
        sheet_names = data.get('sheet_names', [])

        if not isinstance(sheet_names, list):
            return jsonify({"success": False, "error": "参数格式错误"}), 400

        if not sheet_names:
            return jsonify({"success": False, "error": "请选择要删除的章节"}), 400

        # 创建备份
        from ..services import BackupService
        BackupService().create_backup()

        deleted = config_service.batch_delete_chapters(sheet_names)

        return jsonify({
            "success": True,
            "message": f"已删除 {len(deleted)} 个章节",
            "deleted": deleted
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
```

#### 3.4.2 操作类型批量删除

```python
@config_bp.route('/action-library/batch-delete', methods=['POST'])
def batch_delete_actions():
    """批量删除操作类型"""
    try:
        data = request.get_json()
        chapter = data.get('chapter')
        action_names = data.get('action_names', [])

        if not chapter:
            return jsonify({"success": False, "error": "缺少章节参数"}), 400

        if not isinstance(action_names, list):
            return jsonify({"success": False, "error": "参数格式错误"}), 400

        if not action_names:
            return jsonify({"success": False, "error": "请选择要删除的操作类型"}), 400

        # 创建备份
        from ..services import BackupService
        BackupService().create_backup()

        deleted = config_service.batch_delete_chapter_actions(chapter, action_names)

        return jsonify({
            "success": True,
            "message": f"已删除 {len(deleted)} 个操作类型",
            "deleted": deleted
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
```

#### 3.4.3 列映射批量删除

```python
@config_bp.route('/sheet-column-mapping/batch-delete', methods=['POST'])
def batch_delete_mappings():
    """批量删除 Sheet 列映射"""
    try:
        data = request.get_json()
        sheet_names = data.get('sheet_names', [])

        if not isinstance(sheet_names, list):
            return jsonify({"success": False, "error": "参数格式错误"}), 400

        if not sheet_names:
            return jsonify({"success": False, "error": "请选择要删除的 Sheet"}), 400

        # 创建备份
        from ..services import BackupService
        BackupService().create_backup()

        deleted = config_service.batch_delete_sheet_mappings(sheet_names)

        return jsonify({
            "success": True,
            "message": f"已删除 {len(deleted)} 个 Sheet 列映射",
            "deleted": deleted
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
```

---

## 4. 高危关键字同步策略

### 4.1 同步规则

当操作类型改为章节绑定后，高危关键字需要从所有章节中提取：

```python
def _sync_high_risk_keywords(self, config: Dict[str, Any], action_library: Dict[str, Any]) -> None:
    """同步高危关键字列表（从所有章节中提取）"""
    high_risk_keywords = []

    # 遍历所有章节
    for chapter, actions in action_library.items():
        # 遍历该章节的所有操作类型
        for action_name, action_config in actions.items():
            if isinstance(action_config, dict) and action_config.get('is_high_risk', False):
                high_risk_keywords.append(action_name)

    # 去重
    config['high_risk_keywords'] = list(set(high_risk_keywords))
```

### 4.2 rules.yaml 结构示例

```yaml
action_library:
  应用配置:
    新增:
      instruction: "登录配置中心，进入应用配置页面..."
      is_high_risk: false
      render_table: true
    删除:
      instruction: "确认影响范围后，执行删除操作..."
      is_high_risk: true
      render_table: true
      high_risk_note: "删除配置前请备份！"
  容器配置:
    扩容:
      instruction: "进入容器管理平台..."
      is_high_risk: false
      render_table: true
    重启:
      instruction: "重启容器..."
      is_high_risk: true
      render_table: true

high_risk_keywords:
  - 删除
  - 重启
```

---

## 5. 开发任务拆解

### 5.1 后端任务 (Owner: Developer)

| 任务编号 | 任务描述 | 预估工时 |
|----------|----------|----------|
| **V2-B1** | ConfigService 扩展：新增章节操作类型相关方法 | 1h |
| **V2-B2** | ConfigService 扩展：新增批量删除方法 | 0.5h |
| **V2-B3** | ConfigService 扩展：数据格式兼容逻辑 | 0.5h |
| **V2-B4** | API 路由：章节操作类型 API | 1h |
| **V2-B5** | API 路由：批量删除 API | 1h |

### 5.2 前端任务 (Owner: Developer)

| 任务编号 | 任务描述 | 预估工时 |
|----------|----------|----------|
| **V2-F1** | 操作类型页面重构：章节切换交互 | 2h |
| **V2-F2** | 操作类型页面重构：新增/编辑弹窗适配章节 | 1h |
| **V2-F3** | 章节排序页面：添加复选框和批量删除 | 1h |
| **V2-F4** | 操作类型页面：添加复选框和批量删除 | 1h |
| **V2-F5** | 列映射页面：添加复选框和批量删除 | 1h |
| **V2-F6** | 通用组件：批量选择状态管理 | 1h |
| **V2-F7** | 通用组件：批量删除确认弹窗 | 0.5h |

### 5.3 测试任务 (Owner: Tester)

| 任务编号 | 任务描述 | 预估工时 |
|----------|----------|----------|
| **V2-T1** | API 单元测试：章节操作类型 API | 1h |
| **V2-T2** | API 单元测试：批量删除 API | 1h |
| **V2-T3** | 数据迁移测试：旧格式兼容性验证 | 0.5h |
| **V2-T4** | E2E 测试：操作类型章节绑定 | 1h |
| **V2-T5** | E2E 测试：批量删除功能 | 1h |

---

## 6. 验收标准

### 6.1 操作类型与章节绑定

| 验收项 | 通过标准 |
|--------|----------|
| 章节切换 | 点击章节列表切换后，右侧显示该章节的操作类型 |
| 独立配置 | 不同章节可配置同名操作类型，配置独立 |
| 新增操作 | 新增时关联到当前选中章节 |
| 高危同步 | 标记高危后，high_risk_keywords 正确更新 |
| 数据兼容 | 旧格式配置可正常读取，保存后自动转为新格式 |

### 6.2 批量删除功能

| 验收项 | 通过标准 |
|--------|----------|
| 多选交互 | 复选框可正常勾选/取消 |
| 计数显示 | 底部显示"已选择 N 项" |
| 按钮状态 | 未选择时批量删除按钮禁用 |
| 二次确认 | 批量删除前弹出确认弹窗 |
| 删除结果 | 删除成功后列表正确更新，Toast 提示显示 |

---

## 7. 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 数据迁移失败 | 中 | 实现旧格式自动兼容逻辑，保存时统一新格式 |
| 高危关键字遗漏 | 低 | 从所有章节遍历提取，测试覆盖 |
| 前端状态混乱 | 低 | 使用统一的批量选择状态管理器 |
| API 兼容性 | 低 | 保留旧 API，新增章节相关 API |

---

**文档版本**: v2.0
**创建日期**: 2026-02-26
**创建者**: Architect
**更新说明**: 新增操作类型章节绑定、批量删除功能技术方案
