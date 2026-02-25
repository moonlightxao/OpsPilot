# Web 配置中心技术方案

## 1. 需求概述

**来源**: `docs/OpsPilot_PRD.md` 3.4 节

**目标**: 为运维人员提供可视化规则配置界面，替代直接编辑 `config/rules.yaml`

**核心约束**:
- 启动方式: `python main.py web`
- 单人使用，无需并发控制
- 配置即时生效，直接写入 `rules.yaml`

---

## 2. 技术选型

| 层级 | 技术栈 | 选择理由 |
|------|--------|----------|
| **后端框架** | Flask 3.x | 轻量级，与现有 Click CLI 风格一致，单文件可启动 |
| **前端渲染** | Jinja2 + HTMX | 复用 Flask 模板能力，无需前端构建 |
| **样式框架** | TailwindCSS (CDN) | 快速构建 UI，无需 CSS 文件 |
| **富文本编辑** | TinyMCE (CDN) | 支持图片上传，成熟稳定 |
| **拖拽排序** | SortableJS (CDN) | 原生 JS 实现，无依赖 |
| **数据存储** | rules.yaml + backups/ | 复用现有配置，版本控制 |

---

## 3. 目录结构

```
src/
├── web/
│   ├── __init__.py
│   ├── app.py              # Flask 应用工厂
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── config.py       # 配置读写 API
│   │   ├── backup.py       # 备份/回滚 API
│   │   └── upload.py       # 图片上传 API
│   ├── services/
│   │   ├── __init__.py
│   │   ├── config_service.py   # YAML 读写服务
│   │   └── backup_service.py   # 备份管理服务
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── partials/
│       │   ├── chapters.html      # 章节排序
│       │   ├── actions.html       # 操作类型配置
│       │   ├── columns.html       # 列映射配置
│       │   └── backup_modal.html  # 回滚弹窗
│       └── macros/
│           └── form.html          # 表单组件宏

config/
├── rules.yaml             # 主配置（现有）
├── images/                # 新增：富文本图片存储
│   └── .gitkeep
└── backups/               # 新增：配置备份
    └── .gitkeep
```

---

## 4. API 设计

### 4.1 配置管理 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/config` | GET | 获取完整配置 |
| `/api/config` | PUT | 保存完整配置 |
| `/api/config/priority-rules` | GET/PUT | 章节优先级 |
| `/api/config/action-library` | GET/PUT | 操作类型配置 |
| `/api/config/sheet-column-mapping` | GET/PUT | 列映射配置 |
| `/api/config/batch-save` | POST | 批量保存列映射和章节排序 🆕 |

### 4.2 备份管理 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/backups` | GET | 获取备份列表（最近 10 条） |
| `/api/backups/{timestamp}` | GET | 获取指定备份内容 |
| `/api/backups/{timestamp}/restore` | POST | 回滚到指定版本 |

### 4.3 图片上传 API

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/upload/image` | POST | 上传图片，返回 URL |

### 4.4 Excel 上传 API 🆕

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/upload/excel/preview` | POST | 上传 Excel，返回所有 Sheet 及列名预览 |

---

## 5. 数据结构扩展

### 5.1 rules.yaml 扩展

```yaml
# 现有 action_library 扩展
action_library:
  "新增":
    instruction: "在配置管理中心..."
    is_high_risk: false
    render_table: true
    # 新增字段
    images: []                    # 关联图片列表
    high_risk_note: null          # 高危操作注意事项（富文本）
    high_risk_note_images: []     # 高危注意事项图片
```

### 5.2 备份文件命名

```
config/backups/rules.yaml.bak.{YYYYMMDD_HHMMSS}
```

示例: `rules.yaml.bak.20260225_143052`

---

## 6. 核心功能实现

### 6.1 章节排序配置

**前端交互**:
- 使用 SortableJS 实现拖拽排序
- 拖拽结束后自动重新计算优先级（10, 20, 30...）
- 新增章节时，必须填写优先级数值

**数据流**:
```
[拖拽排序] → [SortableJS] → [POST /api/config/priority-rules] → [ConfigService] → [rules.yaml]
```

### 6.2 操作类型配置

**富文本编辑**:
- TinyMCE 配置: `toolbar: 'bold italic | bullist | link | image'`
- 图片上传: TinyMCE → POST `/api/upload/image` → `config/images/` → 返回相对 URL

**高危操作弹窗**:
- 勾选 `is_high_risk` 时，触发弹窗显示高危配置区域
- 保存时自动同步到 `high_risk_keywords` 列表

### 6.3 列映射配置

**手动输入**:
- 使用 tag 形式展示别名
- 点击 × 删除，回车添加

**Excel 辅助识别 - 基础功能**:
- 上传 Excel 文件
- 后端解析第一行表头
- 前端展示可选列表，用户勾选映射

### 6.3.1 Excel 一键保存功能（新增）

**功能概述**: 上传 Excel 后，一键将所有 Sheet 列映射和章节排序保存到配置文件。

**交互流程**:
```
[上传 Excel] → [后端解析所有 Sheet] → [前端展示预览] → [点击"保存到配置"] → [批量更新 rules.yaml]
```

**后端 API 设计**:

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/upload/excel/preview` | POST | 上传 Excel，返回所有 Sheet 及列名预览 |
| `/api/config/batch-save` | POST | 批量保存列映射和章节排序 |

**请求/响应结构**:

```python
# POST /api/upload/excel/preview
# 请求: multipart/form-data (file)
# 响应:
{
    "sheets": [
        {
            "name": "上线安排",
            "columns": ["任务名", "操作类型", "部署单元", "执行人", "复核人"],
            "is_first_sheet": true  # 标记第一个 Sheet
        },
        {
            "name": "上线代码包",
            "columns": ["任务名", "操作类型", "部署单元", "版本号"],
            "is_first_sheet": false
        }
    ],
    "current_priority_rules": ["上线代码包", "应用配置"],  # 已存在的章节
    "max_priority": 20  # 当前最大优先级
}
```

```python
# POST /api/config/batch-save
# 请求:
{
    "sheets": [
        {
            "name": "上线代码包",
            "columns": ["任务名", "操作类型", "部署单元", "版本号"],
            "is_first_sheet": false
        }
    ]
}
# 响应:
{
    "success": true,
    "message": "配置已保存",
    "updated": {
        "sheet_column_mapping": ["上线代码包"],
        "priority_rules": ["上线代码包"]  # 新增的章节
    }
}
```

**保存逻辑**:

```python
def batch_save_sheets(self, sheets: list) -> dict:
    """
    批量保存 Sheet 配置

    规则:
    1. 第一个 Sheet (上线安排) 跳过章节排序，仅保存列映射
    2. 其他 Sheet:
       - 列映射: 始终更新 sheet_column_mapping
       - 章节排序: 仅当 Sheet 名称不存在时才新增
    3. 新增章节的优先级 = 当前最大优先级 + 10
    """
    config = self.load_config()
    updated = {"sheet_column_mapping": [], "priority_rules": []}

    # 获取当前最大优先级
    max_priority = max(
        [p.get("priority", 0) for p in config.get("priority_rules", [])],
        default=0
    )

    for sheet in sheets:
        name = sheet["name"]
        columns = sheet["columns"]
        is_first = sheet.get("is_first_sheet", False)

        # 1. 更新列映射（列名同时作为标准列名和别名）
        column_mapping = {col: [col] for col in columns}
        config["sheet_column_mapping"][name] = column_mapping
        updated["sheet_column_mapping"].append(name)

        # 2. 更新章节排序（仅非第一个 Sheet 且不存在时）
        if not is_first:
            existing_names = [r.get("sheet_name") for r in config.get("priority_rules", [])]
            if name not in existing_names:
                max_priority += 10
                config["priority_rules"].append({
                    "sheet_name": name,
                    "priority": max_priority
                })
                updated["priority_rules"].append(name)

    self.save_config(config)
    return updated
```

**前端交互设计**:

```html
<!-- Excel 上传预览区域 -->
<div id="excel-preview" class="hidden">
    <h3>Excel 预览</h3>
    <div id="sheets-list">
        <!-- 动态生成 Sheet 卡片 -->
    </div>
    <button id="btn-batch-save" class="btn-primary">
        保存到配置
    </button>
</div>
```

**UI 展示结构**:
```
┌─────────────────────────────────────────────────────────┐
│  Excel 预览                                              │
├─────────────────────────────────────────────────────────┤
│  📋 上线安排 (第一个 Sheet - 仅更新列映射)               │
│     列: 任务名, 操作类型, 部署单元, 执行人, 复核人        │
├─────────────────────────────────────────────────────────┤
│  📋 上线代码包 (将新增到章节排序, 优先级: 30)            │
│     列: 任务名, 操作类型, 部署单元, 版本号               │
├─────────────────────────────────────────────────────────┤
│  📋 应用配置 (已存在 - 仅更新列映射)                     │
│     列: 任务名, 操作类型, 配置项, 配置值                 │
├─────────────────────────────────────────────────────────┤
│                          [保存到配置]                    │
└─────────────────────────────────────────────────────────┘
```

### 6.4 配置版本管理

**备份策略**:
```python
class BackupService:
    MAX_BACKUPS = 10

    def create_backup(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"config/backups/rules.yaml.bak.{timestamp}"
        shutil.copy("config/rules.yaml", backup_path)
        self._cleanup_old_backups()

    def _cleanup_old_backups(self):
        # 保留最近 10 个备份
        backups = sorted(Path("config/backups").glob("rules.yaml.bak.*"))
        for old in backups[:-self.MAX_BACKUPS]:
            old.unlink()
```

**回滚流程**:
1. 展示历史版本列表（时间戳 + 差异摘要）
2. 用户选择版本 → 点击回滚
3. 二次确认弹窗
4. 执行回滚 → 覆盖 `rules.yaml`

---

## 7. CLI 命令扩展

在 `main.py` 新增 `web` 命令：

```python
@cli.command()
@click.option('--host', '-h', default='127.0.0.1', help='监听地址')
@click.option('--port', '-p', default=8080, help='监听端口')
@click.option('--no-browser', is_flag=True, help='不自动打开浏览器')
def web(host: str, port: int, no_browser: bool):
    """启动 Web 配置中心"""
    from src.web.app import create_app
    import webbrowser

    app = create_app()

    if not no_browser:
        webbrowser.open(f"http://{host}:{port}")

    click.echo(f"[Web] 配置中心启动: http://{host}:{port}")
    app.run(host=host, port=port, debug=False)
```

---

## 8. 前端页面设计

### 8.1 页面布局

```
┌─────────────────────────────────────────────────────────┐
│  OpsPilot 配置中心                          [预览] [保存] │
├─────────────┬───────────────────────────────────────────┤
│  侧边栏     │  内容区域                                  │
│  ───────    │  ────────────                              │
│  章节排序   │  [当前选中模块的配置界面]                    │
│  操作类型   │                                            │
│  列映射     │                                            │
│  其他配置   │                                            │
│  ───────    │                                            │
│  版本回滚   │                                            │
└─────────────┴───────────────────────────────────────────┘
```

### 8.2 交互规范

| 操作 | 交互方式 |
|------|----------|
| 保存 | 点击保存按钮 → Toast 提示「配置已保存」 |
| 删除 | 二次确认弹窗 |
| 回滚 | 预览差异 → 二次确认 → 执行 |
| 表单校验 | 必填项为空时禁用保存按钮 |

---

## 9. 安全考虑

1. **本地运行**: 仅监听 `127.0.0.1`，不暴露外部网络
2. **无认证**: 单人使用场景，无需登录
3. **文件校验**:
   - 图片上传限制类型（jpg/png/gif）
   - 图片大小限制（5MB）
   - Excel 上传限制大小（10MB）

---

## 10. 依赖新增

```txt
# requirements.txt 新增
flask>=3.0.0
werkzeug>=3.0.0    # Flask 依赖，用于文件上传
```

---

## 11. 开发任务拆解

### 阶段 1: 基础框架 (Owner: Developer)
- [ ] **W1.1** 创建 `src/web/` 目录结构
- [ ] **W1.2** 实现 Flask 应用工厂 `app.py`
- [ ] **W1.3** 实现 `ConfigService` YAML 读写服务
- [ ] **W1.4** 实现 `BackupService` 备份管理服务
- [ ] **W1.5** 在 `main.py` 添加 `web` 命令

### 阶段 2: 核心页面 (Owner: Developer)
- [ ] **W2.1** 实现基础页面模板 (`base.html`, `index.html`)
- [ ] **W2.2** 实现章节排序配置页面
- [ ] **W2.3** 实现操作类型配置页面（含富文本）
- [ ] **W2.4** 实现列映射配置页面
- [ ] **W2.5** 实现图片上传 API

### 阶段 2.6: Excel 一键保存功能 (Owner: Developer) 🆕
- [ ] **W2.6.1** 实现 `/api/upload/excel/preview` API - 解析 Excel 返回所有 Sheet 和列名
- [ ] **W2.6.2** 实现 `/api/config/batch-save` API - 批量保存列映射和章节排序
- [ ] **W2.6.3** 扩展 `ConfigService` 添加 `batch_save_sheets` 方法
- [ ] **W2.6.4** 前端实现 Excel 预览 UI（Sheet 卡片列表）
- [ ] **W2.6.5** 前端实现"保存到配置"按钮及交互逻辑

### 阶段 3: 高级功能 (Owner: Developer)
- [ ] **W3.1** 实现配置保存与备份逻辑
- [ ] **W3.2** 实现版本回滚功能
- [ ] **W3.3** 实现 YAML 预览功能
- [ ] **W3.4** 实现表单校验与 Toast 提示

### 阶段 4: 测试 (Owner: Tester)
- [ ] **W4.1** API 单元测试
- [ ] **W4.2** 端到端测试（Selenium / 手工）
- [ ] **W4.3** 验收测试（对照 PRD 6.2 节）

---

## 12. 验收标准

对照 `docs/OpsPilot_PRD.md` 6.2 节：

| 验收项 | 通过标准 |
|--------|----------|
| 启动与访问 | `python main.py web` 5 秒内启动，浏览器自动打开 |
| 章节排序配置 | 新增必填优先级，拖拽自动重算，保存正确更新 rules.yaml |
| 操作类型配置 | 富文本支持图片，高危弹窗正常，图片保存至 `config/images/` |
| 列映射配置 | 手动输入正常，Excel 辅助识别可选 |
| Excel 一键保存 | 点击"保存到配置"后，所有 Sheet 列映射自动创建/更新；除第一个 Sheet 外自动添加章节排序；已存在 Sheet 不重复添加；优先级自动递增；Toast 提示显示 |
| 配置保存与回滚 | 备份格式正确，最多 10 条，回滚需二次确认 |
| 通用交互 | 必填校验、删除确认、Toast 提示、YAML 预览 |

---

## 13. 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| YAML 解析错误 | 中 | 保存前进行 YAML 语法校验 |
| 图片存储膨胀 | 低 | 设置单图 5MB 限制，定期清理 |
| 浏览器兼容性 | 低 | 使用标准 CDN 资源，兼容主流浏览器 |

---

**文档版本**: v1.1
**创建日期**: 2026-02-25
**更新日期**: 2026-02-25
**创建者**: Architect
**更新说明**: 新增 6.3.1 Excel 一键保存功能技术方案
