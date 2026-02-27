# Web 配置中心技术方案 V4 - 编辑器替换与自动同步

## 1. 变更概述

| 变更项 | 变更前 | 变更后 |
|--------|--------|--------|
| 富文本编辑器 | TinyMCE（部分功能付费） | WangEditor（MIT 协议，完全免费） |
| 核心字段同步 | 手动点击按钮触发 | 保存列映射时自动执行 |

## 2. 富文本编辑器替换方案

### 2.1 技术选型对比

| 特性 | TinyMCE | WangEditor |
|------|---------|------------|
| 协议 | MIT（部分付费） | MIT（完全免费） |
| 图片上传 | 支持 | 支持 |
| 中文支持 | 需加载语言包 | 原生中文 |
| 包大小 | ~500KB（gzip） | ~120KB（gzip） |
| API 风格 | 配置式 | 链式调用 |

### 2.2 前端变更

#### 2.2.1 base.html 修改

**变更位置**：`src/web/templates/base.html` 第 13-14 行

```html
<!-- 删除 TinyMCE CDN -->
- <script src="https://cdn.tiny.cloud/1/no-api-key/tinymce/6/tinymce.min.js" referrerpolicy="origin"></script>

<!-- 新增 WangEditor CDN -->
+ <script src="https://cdn.jsdelivr.net/npm/@wangeditor/editor@5.1.23/dist/index.min.js"></script>
+ <link href="https://cdn.jsdelivr.net/npm/@wangeditor/editor@5.1.23/dist/css/style.min.css" rel="stylesheet">
```

#### 2.2.2 actions.html 修改

**变更位置**：`src/web/templates/partials/actions.html`

**删除内容**（第 423-517 行 TinyMCE 相关代码）：
- `tinymceInitialized` 状态变量
- `initTinyMCE()` 函数
- `ensureTinyMCE()` 函数
- `originalShowAddActionModal` / `originalEditAction` / `originalSaveAction` 覆盖逻辑

**新增内容**：

```javascript
// WangEditor 富文本编辑器
let wangEditorInstance = null;

function initWangEditor() {
    if (wangEditorInstance) {
        wangEditorInstance.destroy();
    }

    const { createEditor, createToolbar } = window.wangEditor;

    // 编辑器配置
    const editorConfig = {
        placeholder: '请输入操作说明...',
        onChange(editor) {
            // 内容变化时自动同步到隐藏 textarea
            document.getElementById('action-instruction').value = editor.getHtml();
        },
        MENU_CONF: {
            uploadImage: {
                server: '/api/upload/image',
                fieldName: 'file',
                maxFileSize: 5 * 1024 * 1024, // 5MB
                allowedFileTypes: ['image/*'],
                customInsert(res, insertFn) {
                    if (res.success && res.url) {
                        insertFn(res.url, res.filename || '', '');
                    }
                },
                onError(file, err) {
                    showToast('图片上传失败: ' + err, 'error');
                }
            }
        }
    };

    // 工具栏配置
    const toolbarConfig = {
        excludeKeys: [
            'group-video',  // 排除视频
            'codeView'      // 排除代码视图
        ]
    };

    // 创建编辑器
    wangEditorInstance = createEditor({
        selector: '#action-instruction-editor',
        html: '',
        config: editorConfig,
        mode: 'default'
    });

    // 创建工具栏
    createToolbar({
        editor: wangEditorInstance,
        selector: '#action-instruction-toolbar',
        config: toolbarConfig,
        mode: 'default'
    });
}

// 设置编辑器内容
function setEditorContent(html) {
    if (wangEditorInstance) {
        wangEditorInstance.setHtml(html || '');
    }
}

// 获取编辑器内容
function getEditorContent() {
    return wangEditorInstance ? wangEditorInstance.getHtml() : '';
}
```

**HTML 结构修改**（弹窗内）：

```html
<!-- 原来的 textarea -->
- <textarea id="action-instruction" class="w-full border rounded px-3 py-2" style="min-height: 200px;"></textarea>

<!-- 改为 WangEditor 容器 -->
+ <div id="action-instruction-toolbar" class="border-b"></div>
+ <div id="action-instruction-editor" style="min-height: 200px;"></div>
+ <input type="hidden" id="action-instruction">
```

### 2.3 后端变更

**无需变更**：图片上传接口 `/api/upload/image` 已存在，WangEditor 兼容现有响应格式。

### 2.4 数据兼容性

WangEditor 与 TinyMCE 产出的 HTML 格式略有不同，但均为标准 HTML：
- TinyMCE：`<p>文本</p>`
- WangEditor：`<p>文本</p>`

**结论**：现有 `instruction` 字段数据无需迁移，直接兼容。

---

## 3. 核心字段自动同步方案

### 3.1 需求变更

| 项目 | 变更前 | 变更后 |
|------|--------|--------|
| 同步时机 | 手动点击「同步到核心字段」按钮 | 保存列映射时自动执行 |
| 按钮状态 | 存在独立按钮 | 移除按钮（或改为隐藏/可选） |
| 交互反馈 | Toast 提示同步结果 | 保存成功时一并提示 |

### 3.2 前端变更

#### 3.2.1 columns.html 修改

**移除同步按钮**（第 7-9 行）：

```html
<!-- 删除 -->
- <button onclick="syncCoreFields()" id="sync-core-fields-btn" class="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600">
-     同步到核心字段
- </button>
```

**修改保存逻辑**（saveSheetMapping 函数）：

```javascript
async function saveSheetMapping() {
    // ... 现有保存逻辑 ...

    try {
        const res = await apiRequest(`/api/config/sheet-column-mapping/${encodeURIComponent(name)}`, 'PUT', sheetConfig);
        if (res.success) {
            // 保存成功后自动同步核心字段
            const syncRes = await apiRequest('/api/config/sync-core-fields', 'POST');

            // 合并提示信息
            const syncCount = syncRes.success ? (syncRes.data?.synced_count || 0) : 0;
            if (syncCount > 0) {
                showToast(`配置已保存，已同步 ${syncCount} 个核心字段`, 'success');
            } else {
                showToast('配置已保存', 'success');
            }

            closeSheetModal();
            loadMappings();
        } else {
            showToast(res.error || '保存失败', 'error');
        }
    } catch (err) {
        showToast('保存失败', 'error');
    }
}
```

**修改批量保存逻辑**（executeBatchSave 函数）：

```javascript
async function executeBatchSave() {
    // ... 现有逻辑 ...

    try {
        const res = await apiRequest('/api/config/batch-save', 'POST', {
            sheets: batchSaveData.sheets
        });

        if (res.success) {
            // 批量保存成功后自动同步核心字段
            const syncRes = await apiRequest('/api/config/sync-core-fields', 'POST');

            const updated = res.updated || {};
            const mappingCount = (updated.sheet_column_mapping || []).length;
            const chapterCount = (updated.priority_rules || []).length;
            const syncCount = syncRes.success ? (syncRes.data?.synced_count || 0) : 0;

            let message = `保存成功！更新 ${mappingCount} 个列映射`;
            if (chapterCount > 0) {
                message += `，新增 ${chapterCount} 个章节`;
            }
            if (syncCount > 0) {
                message += `，同步 ${syncCount} 个核心字段`;
            }

            showToast(message, 'success');
            closeBatchSaveModal();
            loadMappings();
        } else {
            showToast(res.error || '保存失败', 'error');
        }
    } catch (err) {
        showToast('保存失败: ' + err.message, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '保存到配置';
    }
}
```

**移除 syncCoreFields 函数**（第 431-462 行）：
- 该函数逻辑已内联到保存函数中
- 可保留函数定义以备后续调试使用，但移除按钮入口

### 3.3 后端变更

**无需变更**：`/api/config/sync-core-fields` API 已存在，直接调用即可。

### 3.4 交互流程变更

**变更前**：
```
用户编辑列映射 → 点击保存 → Toast "Sheet 映射保存成功" → 用户手动点击同步按钮 → Toast "已同步 N 个核心字段"
```

**变更后**：
```
用户编辑列映射 → 点击保存 → 自动执行同步 → Toast "配置已保存，已同步 N 个核心字段"
```

---

## 4. 任务拆解

### 4.1 开发任务清单

| 序号 | 任务 | 涉及文件 | 预估复杂度 |
|------|------|----------|------------|
| D1 | 替换 base.html 中的编辑器 CDN | `base.html` | 低 |
| D2 | 重写 actions.html 中的 WangEditor 初始化逻辑 | `actions.html` | 中 |
| D3 | 修改 actions.html 中的弹窗 HTML 结构 | `actions.html` | 低 |
| D4 | 移除 columns.html 中的同步按钮 | `columns.html` | 低 |
| D5 | 修改 saveSheetMapping 函数添加自动同步 | `columns.html` | 低 |
| D6 | 修改 executeBatchSave 函数添加自动同步 | `columns.html` | 低 |
| D7 | 清理 columns.html 中废弃的 syncCoreFields 函数 | `columns.html` | 低 |

### 4.2 测试任务清单

| 序号 | 任务 | 验收标准 |
|------|------|----------|
| T1 | WangEditor 基础渲染 | 编辑器正常显示，工具栏完整 |
| T2 | WangEditor 图片上传 | 图片上传成功，正确显示在编辑器中 |
| T3 | WangEditor 内容保存 | 编辑内容正确保存到 instruction 字段 |
| T4 | WangEditor 内容回显 | 编辑已有操作类型时，内容正确回显 |
| T5 | 列映射自动同步（单条） | 保存单个 Sheet 映射后，core_fields 自动更新 |
| T6 | 列映射自动同步（批量） | Excel 一键保存后，core_fields 自动更新 |
| T7 | Toast 提示正确 | 保存成功提示包含同步信息 |
| T8 | 数据兼容性 | 现有 TinyMCE 数据在 WangEditor 中正常显示 |

---

## 5. 风险评估

| 风险项 | 影响 | 缓解措施 |
|--------|------|----------|
| WangEditor CDN 不可用 | 编辑器无法加载 | 可考虑本地化部署或使用 npm |
| 旧数据格式不兼容 | 已保存的富文本显示异常 | 测试覆盖现有数据，必要时做格式转换 |
| 自动同步失败 | 核心字段未更新 | 同步失败时单独提示，不影响主流程 |

---

## 6. 验收标准

### 6.1 富文本编辑器

- [ ] WangEditor 正常加载，无控制台错误
- [ ] 基础格式化功能（加粗、斜体、列表）正常工作
- [ ] 图片上传功能正常，图片保存至 `config/images/`
- [ ] 已保存的 TinyMCE 内容在 WangEditor 中正常显示
- [ ] 新保存的内容格式正确，与 TinyMCE 格式兼容

### 6.2 自动同步

- [ ] 「同步到核心字段」按钮已移除
- [ ] 保存单个 Sheet 映射后，core_fields 自动更新
- [ ] Excel 一键保存后，core_fields 自动更新
- [ ] Toast 提示包含同步信息（如"配置已保存，已同步 N 个核心字段"）
- [ ] 无同步变更时，提示"配置已保存"
- [ ] 同步失败不影响保存主流程

---

## 7. 产出物清单

| 文件 | 变更类型 |
|------|----------|
| `src/web/templates/base.html` | 修改 |
| `src/web/templates/partials/actions.html` | 修改 |
| `src/web/templates/partials/columns.html` | 修改 |

---

**文档版本**: v1.0
**创建日期**: 2026-02-27
**作者**: Architect
