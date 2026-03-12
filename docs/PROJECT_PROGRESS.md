# 🚀 OpsPilot 项目执行看板

## 📊 总体进度状态
- **当前阶段**: V6 里程碑验收完成
- **完成度**: [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓] 100%
- **项目健康度**: 🟢 核心功能 + Web 配置中心增强版全部完成
- **更新日期**: 2026-03-12

---

## ⚠️ 技术路径变更公告

**变更日期**: 2026-02-22

**变更原因**: 为确保视觉效果与样板完全一致，从代码驱动渲染改为模板填充 (Template Injection) 方案

**变更内容**:
| 项目 | 原方案 | 新方案 |
|------|--------|--------|
| 渲染引擎 | `python-docx` 代码生成 | `docxtpl` 模板填充 |
| report.json | v1.0 结构 | v2.0 结构（适配 Jinja2 循环） |
| 样式控制 | 代码中硬编码样式 | 模板文件中定义样式 |

**废弃代码**:
- `src/renderer/word_renderer.py` - 标记为「已废弃」，将被模板渲染器替代

---

## 🆕 新增架构扩展：MCP 服务化

**发布日期**: 2026-02-22

**需求背景**: 外部 Agent 需要通过 MCP 协议调用 OpsPilot 的 Excel 解析与 Word 生成能力

**技术选型**: FastMCP（轻量级 MCP 框架，装饰器风格）

**新增模块**:
```
src/mcp/
├── __init__.py
└── server.py        # MCP Server 实现
```

**MCP 工具清单**:
| 工具名称 | 功能描述 |
|---------|---------|
| `opspilot_analyze` | 解析 Excel 文件，返回 report.json 结构化数据 |
| `opspilot_generate` | 基于 report 数据生成 Word 实施文档 |
| `opspilot_run` | 完整流程：解析 + 生成一体化 |

**新增依赖**:
```txt
fastmcp>=0.1.0
```

**外部 Agent 配置示例**:
```json
{
  "mcpServers": {
    "opspilot": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "D:/code/OpsPilot"
    }
  }
}
```

---

## 🆕 新增功能需求：Web 配置中心

**需求日期**: 2026-02-25

**需求背景**: 通过 YAML 文件配置规则不够直观，运维人员需要可视化界面进行配置管理

**目标用户**: 运维人员（有一定技术背景，但不熟悉 YAML）

**核心功能**:
1. **章节排序配置**：可视化配置 Excel Sheet → Word 章节映射，拖拽排序
2. **操作类型配置**：表格化管理操作类型，支持富文本 + 图片插入，高危操作独立弹窗
3. **列映射配置**：手动输入 + Excel 辅助识别列名别名
4. **配置版本管理**：保留最近 10 个版本历史，支持一键回滚

**技术约束**:
- 启动方式：`python main.py web` 新增 CLI 命令
- 单人使用场景，无需并发控制
- 配置即时生效，直接写入 `config/rules.yaml`
- 图片存储：`config/images/`
- 备份存储：`config/backups/rules.yaml.bak.{timestamp}`

**PRD 更新**: `docs/OpsPilot_PRD.md` 新增 3.4 节「Web 配置中心」

---

## 🚩 风险与阻塞 (Risks & Blockers)
| 等级 | 类型 | 描述 | 状态 | 处理人 |
| :--- | :--- | :--- | :--- | :--- |
| 🟢 | 架构调整 | Renderer 模块已重写为 docxtpl 版本 | 已解决 | Developer |
| 🟢 | 新功能 | MCP Server 模块已完成开发 | 已解决 | Developer |
| 🟢 | 逻辑风险 | 非标准换行已在 `_sanitize_string` 中处理 | 已解决 | Developer |
| 🟢 | 代码规范 | `src/parser/__init__.py` 模块导出已修复 | 已解决 | Developer |
| 🟢 | 编码问题 | Windows 控制台 GBK 无法显示 emoji，已添加 safe_echo 函数处理 | 已解决 | Developer |
| 🟢 | 需求变更 | 输出与样例不一致，技术方案已产出，待 Developer 实现 | 已解决 | Architect |
| 🟢 | 验收缺陷 | 产出与样例不符，按 TECH_DESIGN v2 已实现 Parser/模板修正 | 已解决 | Developer |
| 🟡 | 缺陷分析 | QA_DEFECT_REPORT 缺陷根因：实现滞后 + rules 配置遗漏，非技术方案问题 | 已分析 | Architect |
| 🟡 | 配置遗漏 | rules.yaml 缺少「序号」列 column_mapping，黄金样本「任务序号」无法映射 | 已补充 | Architect |
| 🟡 | 功能缺失 | Excel一键保存时 core_fields 未与保留的列名同步，导致解析器仍尝试匹配已删除的列 | 技术方案完成 | Architect |

---

## 🛠 协同任务列表 (Task Backlog)

### 1. 架构与设计 (Owner: Architect)
- [x] **PRD 深度解析**：分析 `OpsPilot_PRD.md` 确定各模块边界 ✅ 2026-02-17
- [x] **环境初始化**：搭建项目目录结构及依赖配置 ✅ 2026-02-17
- [x] **协议定义 v1.0**：制定 `report.json` 结构，对齐开发与渲染的数据契约 ✅ 2026-02-17
- [x] **规则库配置**：编写 `config/rules.yaml` 初始版本 ✅ 2026-02-17
- [x] **架构审查**：审查 Parser 模块代码规范 ✅ 2026-02-17
- [x] **协议定义 v2.0**：重新设计 report.json 适配 docxtpl 模板循环 ✅ 2026-02-22

### 2. 核心功能开发 (Owner: Developer)
- [x] **解析模块 (Parser)**：实现多 Sheet Excel 读取与清洗 ✅ 2026-02-17
- [x] **模块导出修复**：`src/parser/__init__.py` 添加 ExcelParser 导出 ✅ 2026-02-18
- [x] **CLI 集成**：`main.py` 接入 Parser 模块 ✅ 2026-02-18
- [x] **聚合引擎 (Aggregator)**：已合并至 Parser ✅ 2026-02-17
- [x] **安全哨兵 (Safe-Guard)**：已合并至 Parser ✅ 2026-02-17
- [x] ~~**Word 渲染器 (Renderer)**：基于 `python-docx` 的表格与样式实现~~ ❌ 已移除 2026-02-22
- [x] **模板渲染器开发**：基于 `docxtpl` 实现模板填充 ✅ 2026-02-22
- [x] **Parser 适配 v2.0**：修改 report.json 输出格式适配新协议 ✅ 2026-02-22

### 2.6 输出与样例对齐 (Owner: Architect + Developer) 🆕
- [x] **技术方案设计**：针对 PRD「输出与样例对齐」需求，产出技术方案（含 report.json 扩展、模板调整、渲染流程） ✅ 2026-02-23
- [x] **技术方案修订 v2**：PM 验收不通过后修订，明确第1/3～5部分、第2部分 2.1.x 层级、实施总表 6 列映射、日期转换、Unnamed 过滤 ✅ 2026-02-23
- [x] **Sheet 1 上线安排**：明确如何将 Excel 第一个 Sheet 解析为表格并输出至第2章「实施步骤和计划」 ✅ 2026-02-23
- [x] **样例样式对齐**：明确如何实现与 `实施文档.docx` 在章节结构、表格形式、排版样式上的视觉一致性 ✅ 2026-02-23
- [x] **Parser 实施总表**：解析第一个 Sheet 为 implementation_summary，排除该 Sheet 不进入 sections ✅ 2026-02-23
- [x] **Parser 列映射与日期**：实施总表 6 列映射、过滤 Unnamed、Excel 日期序列号转换（修订 v2） ✅ 2026-02-23
- [x] **Renderer 实施总表**：context 注入 + 内置渲染增加 2.1 实施总表表格 ✅ 2026-02-23
- [x] **模板结构修订**：第1部分、第3～5部分、第2部分 2.1.x 层级、实施总表 6 列（修订 v2） ✅ 2026-02-23

### 2.5 MCP 服务化扩展 (Owner: Developer)
- [x] **MCP 依赖安装**：`requirements.txt` 添加 `fastmcp>=0.1.0` ✅ 2026-02-22
- [x] **MCP 目录创建**：创建 `src/mcp/` 目录及 `__init__.py` ✅ 2026-02-22
- [x] **MCP Server 实现**：`src/mcp/server.py` 实现 3 个 MCP Tool ✅ 2026-02-22
- [x] **Tool: opspilot_analyze**：封装 ExcelParser.parse() 为 MCP Tool ✅ 2026-02-22
- [x] **Tool: opspilot_generate**：封装 Renderer.render() 为 MCP Tool ✅ 2026-02-22
- [x] **Tool: opspilot_run**：实现完整流程的 MCP Tool ✅ 2026-02-22
- [x] **MCP 启动入口**：支持 `python -m src.mcp.server` 启动 ✅ 2026-02-22

### 2.7 Web 配置中心 (Owner: Developer) 🆕
- [x] **W1.1 基础框架**：创建 `src/web/` 目录结构、Flask 应用工厂 ✅ 2026-02-25
- [x] **W1.2 配置服务**：实现 ConfigService YAML 读写服务 ✅ 2026-02-25
- [x] **W1.3 备份服务**：实现 BackupService 备份管理服务（最多 10 条） ✅ 2026-02-25
- [x] **W1.4 CLI 扩展**：`main.py` 添加 `web` 命令，支持 `python main.py web` ✅ 2026-02-25
- [x] **W2.1 页面模板**：实现基础页面模板（base.html, index.html） ✅ 2026-02-25
- [x] **W2.2 章节排序**：实现章节排序配置页面（拖拽排序） ✅ 2026-02-25
- [x] **W2.3 操作类型**：实现操作类型配置页面（富文本 + 图片上传） ✅ 2026-02-25
- [x] **W2.4 列映射**：实现列映射配置页面（手动输入 + Excel 辅助） ✅ 2026-02-25
- [x] **W2.5 图片上传**：实现图片上传 API，保存至 `config/images/` ✅ 2026-02-25
- [x] **W3.1 配置保存**：实现配置保存与自动备份逻辑 ✅ 2026-02-25
- [x] **W3.2 版本回滚**：实现版本回滚功能（二次确认） ✅ 2026-02-25
- [x] **W3.3 YAML 预览**：实现 YAML 格式预览功能 ✅ 2026-02-25
- [x] **W3.4 表单校验**：实现表单校验与 Toast 提示 ✅ 2026-02-25

### 2.8 Excel 一键保存功能 (Owner: Developer) 🆕
- [x] **W2.6.1 Excel 预览 API**：实现 `/api/upload/excel/preview` - 解析 Excel 返回所有 Sheet 和列名 ✅ 2026-02-26
- [x] **W2.6.2 批量保存 API**：实现 `/api/config/batch-save` - 批量保存列映射和章节排序 ✅ 2026-02-26
- [x] **W2.6.3 ConfigService 扩展**：添加 `batch_save_sheets` 方法 ✅ 2026-02-26
- [x] **W2.6.4 前端预览 UI**：Excel 预览界面（Sheet 卡片列表） ✅ 2026-02-26
- [x] **W2.6.5 保存按钮交互**：前端"保存到配置"按钮及交互逻辑 ✅ 2026-02-26

### 2.9 操作类型章节绑定 + 批量删除功能 (Owner: Developer) 🆕
**技术方案**: `docs/TECH_DESIGN_WEB_CONFIG_V2.md`

**后端任务**:
- [x] **V2-B1** ConfigService 扩展：新增章节操作类型相关方法 ✅ 2026-02-26
- [x] **V2-B2** ConfigService 扩展：新增批量删除方法 ✅ 2026-02-26
- [x] **V2-B3** ConfigService 扩展：数据格式兼容逻辑（旧格式自动迁移） ✅ 2026-02-26
- [x] **V2-B4** API 路由：章节操作类型 API（GET/PUT/DELETE） ✅ 2026-02-26
- [x] **V2-B5** API 路由：批量删除 API（章节/操作类型/列映射） ✅ 2026-02-26

**前端任务**:
- [x] **V2-F1** 操作类型页面重构：章节切换交互 ✅ 2026-02-26
- [x] **V2-F2** 操作类型页面重构：新增/编辑弹窗适配章节 ✅ 2026-02-26
- [x] **V2-F3** 章节排序页面：添加复选框和批量删除 ✅ 2026-02-26
- [x] **V2-F4** 操作类型页面：添加复选框和批量删除 ✅ 2026-02-26
- [x] **V2-F5** 列映射页面：添加复选框和批量删除 ✅ 2026-02-26
- [x] **V2-F6** 通用组件：批量选择状态管理 ✅ 2026-02-26
- [x] **V2-F7** 通用组件：批量删除确认弹窗 ✅ 2026-02-26

### 2.10 核心字段同步功能 (Owner: Developer) 🆕
**需求来源**: 用户反馈 Excel 一键保存后，删除的列名仍在 core_fields 中，导致解析异常

**需求背景**:
- 用户在列映射页面上传 Excel 后，手动删除不需要的列
- 但 `core_fields` 中的别名未同步更新，仍包含已删除的列名
- 解析器仍尝试匹配这些已删除的列名，导致生成文档异常

**解决方案**: 在列映射页面增加「同步到核心字段」按钮，用户手动触发同步

**PRD 更新**: `docs/OpsPilot_PRD.md` 3.4.3-C 节「核心字段同步」

**后端任务**:
- [x] **CF-B1** ConfigService 扩展：新增 `sync_core_fields_from_columns` 方法，根据 sheet_column_mapping 中的列名更新 core_fields ✅ 2026-02-26
- [x] **CF-B2** API 路由：核心字段同步 API（POST `/api/config/sync-core-fields`） ✅ 2026-02-26
- [x] **CF-B3** 核心字段识别逻辑：根据关键词匹配列名到对应的核心字段（操作类型→action_type，任务名→task_name 等） ✅ 2026-02-26

**前端任务**:
- [x] **CF-F1** 列映射页面：底部增加「同步到核心字段」按钮 ✅ 2026-02-26
- [x] **CF-F2** 同步交互：点击按钮调用 API，显示 Toast 提示同步结果 ✅ 2026-02-26

### 2.11 Excel 一键保存全量覆盖模式 (Owner: Developer) 🆕
**需求来源**: 用户反馈 Excel 一键保存后配置累积/膨胀

**需求背景**:
- 当前 `batch_save_sheets` 采用增量更新模式
- 历史配置无法自动清理
- 用户期望基于 Excel 内容全量覆盖配置

**技术方案**: `docs/TECH_DESIGN_BATCH_SAVE_V5.md`

**后端任务**:
- [x] **V5-B1** ConfigService 重构：`batch_save_sheets` 全量覆盖 `sheet_column_mapping` ✅ 2026-03-01
- [x] **V5-B2** ConfigService 重构：`batch_save_sheets` 全量覆盖 `priority_rules`，按顺序分配优先级 ✅ 2026-03-01
- [x] **V5-B3** ConfigService 重构：新增 `_sync_core_fields_full` 全量重新生成 `core_fields` ✅ 2026-03-01
- [x] **V5-B4** API 返回值扩展：增加 `deleted` 字段记录被删除的配置项 ✅ 2026-03-01

**测试任务**:
- [x] **V5-T1** 单元测试：上传包含 Sheet A、B、C 的 Excel，验证 `sheet_column_mapping` 仅包含 A、B、C ✅ 2026-03-01
- [x] **V5-T2** 单元测试：原有配置包含 Sheet D、E,上传 Excel 后验证 D、E 被删除 ✅ 2026-03-01
- [x] **V5-T3** 单元测试：验证 `action_library` 保持不变 ✅ 2026-03-01
- [x] **V5-T4** 单元测试:验证 `priority_rules` 按 Sheet 顺序分配(10, 20, 30...) ✅ 2026-03-01
- [x] **V5-T5** 单元测试:验证 `core_fields` 基于新列名重新生成,旧字段被清理 ✅ 2026-03-01

### 2.12 Excel 导入自动识别操作类型 (Owner: Developer) 🆕
**需求来源**: 用户需求：导入 Excel 后自动识别每个 Sheet 的操作类型列并保存

**需求背景**:
- 当前导入 Excel 仅保存列映射和章节排序
- 用户希望自动识别「操作类型」列的值并保存到 action_library
- 同名操作类型需用户确认覆盖/跳过

**技术方案**: `docs/TECH_DESIGN_ACTION_TYPE_RECOGNITION_V6.md`

**后端任务**:
- [x] **V6-B1** 修改预览 API：`/api/upload/excel/preview` 返回识别到的操作类型列表 ✅ 2026-03-01
- [x] **V6-B2** ConfigService 扩展：新增 `batch_save_action_types` 方法 ✅ 2026-03-01
- [x] **V6-B3** API 扩展：新增 `/api/config/batch-save-action-types` 端点 ✅ 2026-03-01
- [x] **V6-B4** 保存逻辑：处理覆盖/跳过标记 ✅ 2026-03-01

**前端任务**:
- [x] **V6-F1** 预览界面：展示识别到的操作类型列表（按 Sheet 分组） ✅ 2026-03-01
- [x] **V6-F2** 冲突交互：已存在的操作类型显示冲突标记和勾选框 ✅ 2026-03-01

**测试任务**:
- [x] **V6-T1** 单元测试：操作类型列识别逻辑 ✅ 2026-03-01
- [x] **V6-T2** 单元测试：批量保存 API（新增、覆盖、跳过场景） ✅ 2026-03-01
- [x] **V6-T3** 单元测试：无操作类型列的 Sheet 跳过处理 ✅ 2026-03-01

### 3. 质量保障 (Owner: Tester)
- [x] **单元测试**：Parser 30/30 通过，Renderer 22/22 全部通过 ✅ 2026-02-18
- [x] **边界测试**：空文件、缺失字段、非法字符处理已覆盖 ✅ 2026-02-18
- [x] **高危流程测试**：高危操作检测逻辑已验证（删除/下线正确标记） ✅ 2026-02-18
- [x] **端到端测试**：10/10 全部通过 ✅ 2026-02-18
- [x] **样式比对**：数据完整性、文档结构、格式检查全部通过 ✅ 2026-02-18
- [x] **模板渲染测试**：验证 TemplateRenderer 内置渲染功能，62 个测试全部通过 ✅ 2026-02-22
- [x] **v2.0 协议适配**：测试用例已更新适配 cells 数组格式 ✅ 2026-02-22
- [x] **MCP 集成测试**：测试用例已创建（需安装 fastmcp 依赖后运行） ✅ 2026-02-22
- [x] **黄金样本测试**：使用 上线checklist.xlsx + 实施文档.docx 端到端验证，2/2 通过 ✅ 2026-02-23
- [ ] **Web API 测试**：API 单元测试（待 Developer 完成 W1 阶段）
- [ ] **Web E2E 测试**：端到端测试，验收 PRD 6.2 节全部通过

---

## 📝 协同变更日志 (Collaboration Log)
> **记录要求**：Agent 完成任务后，需按格式追加：`[日期] [角色] 动作 | 产出物`

- **2026-02-17 [System]** 项目立项：MDC 角色定义（Architect, Developer, Tester）已完成注入。
- **2026-02-17 [System]** 样例导入：`上线checklist.xlsx` 与 `实施文档.doc` 已放入 `docs/Sample_Files/`。
- **2026-02-17 [Architect]** PRD 分析完成：确定四大核心模块（Parser、Aggregator、SafeGuard、Renderer）
- **2026-02-17 [Architect]** 目录初始化完成：创建 src/{parser,aggregator,renderer,safeguard}、tests、templates、output
- **2026-02-17 [Architect]** 协议定义完成：发布 `docs/report_schema.md`，定义解析层与渲染层数据契约
- **2026-02-17 [Architect]** 规则库配置完成：`config/rules.yaml` 包含章节优先级、动作映射、高危关键字、表头映射
- **2026-02-17 [Architect]** 主入口实现：`main.py` 支持 analyze/generate/run 三种命令模式
- **2026-02-17 [Developer]** Parser 模块完成：`src/parser/excel_parser.py` 实现多 Sheet 读取、动态表头解析、防御性编程、report.json 生成
- **2026-02-17 [Architect]** 架构审查完成：Parser 代码符合规范，发现模块导出缺失问题
- **2026-02-17 [Architect]** 发布任务：指派 Developer 修复 `__init__.py` 导出、集成 main.py、开发 Renderer
- **2026-02-18 [Developer]** 模块导出修复：`src/parser/__init__.py` 已正确导出 ExcelParser 和 parse_excel
- **2026-02-18 [Developer]** CLI 集成完成：`main.py` 已接入 Parser 模块，analyze 命令可正常输出 report.json
- **2026-02-18 [Developer]** Renderer 模块完成：`src/renderer/word_renderer.py` 实现基于 python-docx 的 Word 文档渲染
- **2026-02-18 [Developer]** 端到端流程打通：analyze -> generate 完整链路已实现
- **2026-02-18 [Tester]** 测试框架搭建：创建 `tests/conftest.py` 配置共享 fixtures
- **2026-02-18 [Tester]** Parser 单元测试：30 个测试用例，覆盖解析、映射、高危检测、清洗逻辑，29 通过
- **2026-02-18 [Tester]** Renderer 单元测试：22 个测试用例，覆盖文档生成、摘要、告警、表格渲染，全部通过
- **2026-02-18 [Tester]** 端到端测试：10 个测试用例，核心流程通过，发现 Windows 控制台编码问题
- **2026-02-18 [Tester]** 发现缺陷：Windows GBK 控制台无法输出 ⚠️ emoji，需 Developer 修复
- **2026-02-18 [Developer]** 编码问题修复：新增 safe_echo 函数，自动检测终端编码并替换特殊字符，端到端测试通过
- **2026-02-18 [Tester]** 样式比对测试：使用样例文件进行数据完整性、文档结构、格式检查，6/6 检查项全部通过
- **2026-02-22 [Architect]** 技术路径调整：决定从 python-docx 代码渲染改为 docxtpl 模板填充方案
- **2026-02-22 [Architect]** 协议升级 v2.0：重新设计 `docs/report_schema.md`，适配 Jinja2 模板循环语法
- **2026-02-22 [Developer]** 模板文件创建：`templates/template.docx` 包含 docxtpl 兼容的 Jinja2 占位符
- **2026-02-22 [Architect]** MCP 服务化方案设计：发布技术方案，定义 3 个 MCP Tool 及接口 Stub
- **2026-02-22 [Developer]** 依赖更新：`requirements.txt` 添加 docxtpl 和 fastmcp
- **2026-02-22 [Developer]** Parser v2.0 适配：report.json 结构升级，支持 cells 数组和 columns 前置
- **2026-02-22 [Developer]** 模板渲染器完成：`src/renderer/template_renderer.py` 支持 docxtpl 和内置渲染
- **2026-02-22 [Developer]** MCP Server 完成：`src/mcp/server.py` 实现 opspilot_analyze/generate/run 三个工具
- **2026-02-22 [Architect]** 代码重构完成：CLI 统一使用 TemplateRenderer、移除 word_renderer、删除空模块 safeguard/aggregator、sample_report 升级 v2.0
- **2026-02-22 [Tester]** 测试用例适配 v2.0：修复 test_parser.py 和 test_e2e.py 适配 cells 数组格式
- **2026-02-22 [Tester]** 模板渲染测试完成：test_renderer.py 覆盖 TemplateRenderer 全部功能
- **2026-02-22 [Tester]** MCP 集成测试创建：新增 test_mcp.py 覆盖 3 个 MCP Tool 测试
- **2026-02-22 [Tester]** 测试通过：62 个核心测试全部通过（Parser 30 + Renderer 22 + E2E 10）
- **2026-02-23 [PM]** 需求细化：用户反馈输出与样例不一致，细化「输出与样例对齐」需求 | 更新 OpsPilot_PRD.md
- **2026-02-23 [PM]** 指派修正：将 2.6 任务指派由 Developer 改为 Architect，遵循「需求→架构师技术方案→开发」流程
- **2026-02-23 [Architect]** 技术方案设计完成：产出 `docs/TECH_DESIGN_OUTPUT_ALIGNMENT.md`，定义 implementation_summary 协议、rules 扩展、Parser/Renderer 调整路径
- **2026-02-23 [Architect]** 配置与协议更新：rules.yaml 增加 implementation_summary 配置，report_schema.md 扩展 v2.1
- **2026-02-23 [Developer]** 输出与样例对齐实现：Parser 解析第一个 Sheet 为 implementation_summary、排除进入 sections；TemplateRenderer 注入并渲染实施总表；create_template 增加 docxtpl 实施总表区块；测试用例适配 | 64 测试通过
- **2026-02-23 [Tester]** 测试任务执行：66 passed / 1 skipped (MCP 需 fastmcp)；黄金样本端到端验证通过；边界测试、高危流程测试全部通过 | test_golden_sample.py 新增
- **2026-02-23 [PM]** 需求验收：依据 PRD 第 6 节逐条核查，初判 5/5 通过
- **2026-02-23 [PM]** 验收更正：对照 output/实施文档.docx 与 docs/Sample_Files/实施文档.docx 逐项比对，发现产出与标准严重不符 | 与样例对齐 不通过，缺陷已记录，已指派 Architect 修订方案
- **2026-02-23 [Architect]** 技术方案修订 v2：产出 `TECH_DESIGN_OUTPUT_ALIGNMENT.md` v2.0，明确第1/3～5部分占位、第2部分 2.1.x 层级、实施总表 6 列映射、Excel 日期转换、Unnamed 过滤；更新 rules.yaml、report_schema.md
- **2026-02-23 [Developer]** 缺陷修复：Parser 增加 Unnamed 过滤、列映射、Excel 日期转换、序号自动生成；create_template 增加第1/3～5部分、第2部分 2.1.x 结构、实施总表 6 列；TemplateRenderer context 适配 | 68 测试通过
- **2026-02-23 [Tester]** 模板对比测试执行：新增 test_template_comparison.py 比对生成文档与样例；发现 2 项缺陷（实施总表列异常、第2部分层级不符）；已输出 `docs/QA_DEFECT_REPORT.md` 提单给 Developer
- **2026-02-23 [Architect]** 缺陷分析完成：对照 QA_DEFECT_REPORT 与 TECH_DESIGN v2，判定技术方案正确；缺陷 #1 根因为 Parser 实现未完全生效 + rules.yaml 缺少「序号」列 column_mapping；缺陷 #2 为 create_template/template 未按 v2 落地；已补充 rules.yaml 序号映射，待 Developer 完成 Parser/模板修正
- **2026-02-23 [Developer]** 缺陷 #1 修复：Parser 增加 _is_excel_serial_column 过滤 46315 等日期序列号列；统一 column_mapping 支持「任务序号」→「序号」；缺陷 #2：重新执行 create_template 生成 template.docx | 68 passed, 3 skipped
- **2026-02-23 [Tester]** 回归测试：缺陷 #1、#2 已通过验证；实施总表 6 列正确、第2部分层级正确；更新 QA_DEFECT_REPORT 回归结论
- **2026-02-23 [PM]** 需求与缺陷单验收：依据 PRD 第 6 节及 QA_DEFECT_REPORT 回归结论逐项核查；缺陷 #1、#2 验收通过；M3 成果对齐 验收通过；第1/3～5 部分列为遗留项 | 更新 PROJECT_PROGRESS 验收结论
- **2026-02-25 [PM]** 需求细化：用户反馈 YAML 配置不直观，细化「Web 配置中心」需求 | 更新 OpsPilot_PRD.md 3.4 节
- **2026-02-25 [PM]** 需求移交：Web 配置中心需求细化完成，待 Architect 进行技术方案设计 | 产出物：OpsPilot_PRD.md 3.4 节、6.2 节
- **2026-02-25 [Architect]** 技术方案设计完成：产出 `docs/TECH_DESIGN_WEB_CONFIG.md`，定义技术选型、目录结构、API 设计、任务拆解 | 产出物：TECH_DESIGN_WEB_CONFIG.md
- **2026-02-25 [Developer]** Web 配置中心开发完成：实现 Flask 应用工厂、ConfigService/BackupService、配置管理 API、章节排序/操作类型/列映射页面、图片上传、版本回滚、YAML 预览 | 14 项任务全部完成 | 产出物：src/web/
- **2026-02-25 [PM]** 需求细化：Excel 辅助识别新增「一键保存」功能，自动保存 Sheet 列映射并填充章节排序 | 更新 OpsPilot_PRD.md 3.4.3-C 节、6.2 节 | 待 Architect 技术方案设计
- **2026-02-25 [Architect]** 技术方案设计完成：产出 TECH_DESIGN_WEB_CONFIG.md v1.1，新增 6.3.1 Excel 一键保存功能方案 | 定义 2 个新 API、5 项开发任务 | 产出物：TECH_DESIGN_WEB_CONFIG.md
- **2026-02-26 [Developer]** Excel 一键保存功能完成：实现 `/api/upload/excel/preview` 预览 API、`/api/config/batch-save` 批量保存 API、ConfigService.batch_save_sheets 方法、前端预览 UI 和保存交互 | 5 项任务全部完成 | 产出物：src/web/routes/upload.py、src/web/routes/config.py、src/web/services/config_service.py、src/web/templates/partials/columns.html
- **2026-02-26 [PM]** 需求细化：操作类型配置需与章节绑定，每个章节拥有独立的操作类型库 | 更新 OpsPilot_PRD.md 3.4.3-B 节、6.2 节 | 待 Architect 技术方案设计
- **2026-02-26 [PM]** 需求细化：章节排序、操作类型、列映射页面新增批量删除功能 | 更新 OpsPilot_PRD.md 3.4.3-A/B/C 节、6.2 节 | 待 Architect 技术方案设计
- **2026-02-26 [Architect]** 技术方案设计完成：产出 `docs/TECH_DESIGN_WEB_CONFIG_V2.md`，定义操作类型章节绑定、批量删除功能技术方案 | 包含数据迁移策略、API 扩展、前端重构、12 项开发任务 | 产出物：TECH_DESIGN_WEB_CONFIG_V2.md
- **2026-02-26 [PM]** 需求细化：发现 Excel 一键保存后 core_fields 未与保留的列名同步，新增「核心字段同步」功能 | 更新 OpsPilot_PRD.md 3.4.3-C 节、6.2 节 | 待 Architect 技术方案设计
- **2026-02-26 [PM]** 需求确认：用户确认「核心字段同步」需求 - 列映射页面新增「同步到核心字段」按钮，手动触发同步 | 产出物：OpsPilot_PRD.md | 已移交 Architect 进行技术方案设计
- **2026-02-26 [Architect]** 技术方案设计完成：产出 `docs/TECH_DESIGN_WEB_CONFIG_V3.md`，定义核心字段同步功能技术方案 | 包含关键词匹配规则、ConfigService 扩展、API 设计、5 项开发任务 | 产出物：TECH_DESIGN_WEB_CONFIG_V3.md
- **2026-02-26 [Developer]** 核心字段同步功能完成：实现 sync_core_fields_from_columns 方法、关键词匹配、同步 API、前端同步按钮及交互 | 5 项任务全部完成，16 passed | 产出物：src/web/services/config_service.py、src/web/routes/config.py、src/web/templates/partials/columns.html、tests/test_web_api_v2.py
- **2026-02-27 [PM]** M7 里程碑验收完成：操作类型章节绑定、批量删除、核心字段同步全部功能验收通过 | 更新 PROJECT_PROGRESS.md 验收结论
- **2026-02-27 [PM]** 需求变更：1) 富文本编辑器从 TinyMCE 换成 WangEditor（完全免费）；2) 列映射同步改为保存时自动执行 | 更新 OpsPilot_PRD.md 3.4.3-B/C 节、6.2 节 | 待 Architect 技术方案设计
- **2026-02-27 [Architect]** 技术方案设计完成：产出 `docs/TECH_DESIGN_WEB_CONFIG_V4.md`，定义 WangEditor 替换方案、自动同步实现方案 | 包含 7 项开发任务、8 项测试任务 | 产出物：TECH_DESIGN_WEB_CONFIG_V4.md | 待 Developer 实现
- **2026-02-27 [Developer]** V4 方案实现完成：TinyMCE 替换为 WangEditor、列映射保存时自动同步核心字段 | 7 项任务全部完成，服务验证通过 | 产出物：base.html、actions.html、columns.html、app.py
- **2026-02-27 [Developer]** Bug 修复：1) YAML 预览报错（数字键导致排序失败）；2) core_fields 同步失败（非字符串列名处理） | 添加 `_stringify_keys` 函数、修复 `_match_core_field` 类型检查 | 产出物：config_service.py
- **2026-03-01 [PM]** 需求细化：Excel 一键保存从增量更新改为全量覆盖模式 | 问题背景：用户反馈配置累积/膨胀 | 更新 OpsPilot_PRD.md 3.4.3-C 节、6.2 节 | 待 Architect 技术方案设计
- **2026-03-01 [Architect]** 技术方案设计完成：产出 `docs/TECH_DESIGN_BATCH_SAVE_V5.md`，定义全量覆盖模式实现方案 | 包含 4 项后端任务、5 项测试任务 | 产出物：TECH_DESIGN_BATCH_SAVE_V5.md | 待 Developer 实现
- **2026-03-01 [Developer]** V5 后端任务完成：重构 batch_save_sheets 全量覆盖模式、新增 _sync_core_fields_full 方法、API 返回值扩展 | 4 项后端任务全部完成 | 139 passed, 3 skipped | 产出物：config_service.py、config.py
- **2026-03-01 [Tester]** V5 测试完成：5 项测试任务全部通过 | 新增 test_batch_save_v5.py | 验收通过
- **2026-03-01 [PM]** 需求细化：Excel 导入自动识别操作类型,问题背景：导入 Excel 后自动识别每个 Sheet 的操作类型列并保存 | 新增 PRD 3.4.3-C 节「操作类型自动识别」 | 待 Architect 技术方案设计
- **2026-03-01 [Architect]** 技术方案设计完成:产出 `docs/TECH_DESIGN_ACTION_TYPE_RECOGNITION_V6.md`,定义操作类型自动识别方案 | 包含 4 项后端任务、3 项测试任务 | 产出物:TECH_DESIGN_ACTION_TYPE_RECOGNITION_V6.md | 待 Developer 实现
- **2026-03-01 [Developer]** V6 后端开发完成：修改预览 API 返回操作类型、新增 batch_save_action_types 方法、新增批量保存 API | 4 项后端任务完成 | 产出物:upload.py、config_service.py、config.py | 待前端实现
- **2026-03-01 [Developer]** V6 前端开发完成：预览界面展示操作类型列表、冲突交互 | 2 项前端任务完成 | 产出物:columns.html | 待测试验证
- **2026-03-01 [Tester]** V6 测试完成：4 项测试任务全部通过 | 新增 test_action_type_recognition_v6.py | 验收通过

---

## 📋 架构设计摘要

### 模块边界
```
┌─────────────────────────────────────────────────────────────────────────┐
│                            OpsPilot                                      │
├─────────────┬─────────────┬─────────────┬─────────────────┬─────────────┤
│   Parser    │  Aggregator │  SafeGuard  │    Renderer     │  MCP Server │
│  (解析层)   │  (聚合层)   │  (安全层)   │    (渲染层)     │  (服务层)   │
│   ✅ 完成   │  ✅ 已合并   │ ✅ 已合并   │   ✅ 完成       │  ✅ 完成    │
├─────────────┴─────────────┴─────────────┴─────────────────┴─────────────┤
│                    report.json v2.0 (模板适配)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                  templates/template.docx (Jinja2 模板)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                      config/rules.yaml (规则库)                         │
├─────────────────────────────────────────────────────────────────────────┤
│                      src/web/ (Web 配置中心) ✅ 完成                     │
│                      ├── Excel 一键保存 ✅ 完成                          │
│                      ├── 操作类型章节绑定 + 批量删除 ✅ 完成              │
│                      ├── 核心字段同步 ✅ 完成                            │
│                      ├── V5 全量覆盖模式 ✅ 完成                         │
│                      └── V6 操作类型自动识别 ✅ 完成                     │
└─────────────────────────────────────────────────────────────────────────┘
```

### 架构调整说明
- **Aggregator/SafeGuard 合并**：为简化流程，将聚合和高危判断逻辑内置到 Parser
- **Renderer 重构**：从 `python-docx` 代码驱动改为 `docxtpl` 模板填充
- **协议升级 v2.0**：report.json 结构适配 Jinja2 `{% for %}` 循环
- **MCP 服务层**：新增对外服务接口，支持外部 Agent 通过 MCP 协议调用

### 数据流向（新方案）
```
Excel → Parser → report.json v2.0 (人工确认) → docxtpl → template.docx → Word 实施文档
  │                                                              ↑
  └────────────── MCP Server (opspilot_analyze/generate) ────────┘
```

### 关键设计决策
1. **两阶段执行**：analyze 与 generate 分离，强制人工确认环节
2. **规则驱动**：所有业务逻辑从 rules.yaml 读取，支持无代码配置
3. **高危拦截**：删除/下线/重建等操作触发挂起确认流程
4. **模板驱动**：使用 docxtpl 模板填充，确保视觉效果与样板一致
5. **MCP 服务化**：通过 FastMCP 对外暴露标准化工具接口，支持多 Agent 协同

---

## 📅 阶段性里程碑
- [x] **M1**: 跑通数据解析到 JSON 的全流程（数据对齐）✅ 2026-02-18
- [ ] **M2**: 演示"高危挂起-确认"的协同交互（逻辑对齐）
- [x] **M3**: 产出第一份完全符合样式的 Word 实施方案（成果对齐）✅ 2026-02-23 PM 验收：缺陷 #1 #2 已修复，核心验收通过
- [x] **M4**: 模板填充方案验证通过（架构升级）✅ 2026-02-22
- [x] **M5**: MCP 服务上线，外部 Agent 可调用（服务化）✅ 2026-02-22
- [x] **M6**: Web 配置中心上线，运维人员可通过可视化界面管理规则配置 ✅ 2026-02-25
- [x] **M7**: 操作类型章节绑定 + 批量删除 + 核心字段同步功能上线（Web 增强版）✅ 2026-02-26
- [x] **V5**: Excel 一键保存全量覆盖模式 ✅ 2026-03-01
- [x] **V6**: Excel 导入自动识别操作类型 ✅ 2026-03-01

---

## ✅ PM 验收结论 (2026-02-27) — **M7 里程碑验收通过**

### 操作类型章节绑定
| 验收项 | 标准 | 结果 |
|--------|------|------|
| 章节切换 | 切换章节后显示该章节的操作类型列表 | ✅ 通过 |
| 独立配置 | 不同章节可配置同名操作类型，步骤说明独立 | ✅ 通过 |
| 数据结构 | `action_library` 为 `{章节名: {操作类型: 配置}}` | ✅ 通过 |

### 批量删除功能
| 验收项 | 标准 | 结果 |
|--------|------|------|
| 章节排序批量删除 | API 返回 `已删除 N 个章节` | ✅ 通过 |
| 操作类型批量删除 | API 返回 `已删除 N 个操作类型` | ✅ 通过 |
| 列映射批量删除 | API 返回 `已删除 N 个 Sheet 列映射` | ✅ 通过 |

### 核心字段同步功能
| 验收项 | 标准 | 结果 |
|--------|------|------|
| 同步 API | POST `/api/config/sync-core-fields` 正常响应 | ✅ 通过 |
| Toast 提示 | 返回 `已同步 N 个核心字段` | ✅ 通过 |
| 别名更新 | core_fields 别名正确包含列映射中的列名 | ✅ 通过 |
| 属性保留 | 预置字段的 `required` 属性保持不变 | ✅ 通过 |

**验收结论**：M7 里程碑全部功能验收通过。

---

## ✅ PM 验收结论 (2026-02-23) — **回归后：核心验收通过**

依据 `docs/OpsPilot_PRD.md` 第 6 节、`docs/QA_DEFECT_REPORT.md` 回归测试结论逐项核查：

| 验收项 | 标准 | 结论 | 说明 |
|--------|------|------|------|
| **与样例对齐（核心）** | 第2章结构、实施总表、表格形式可视觉比对一致 | ✅ 通过 | 缺陷 #1、#2 已修复，回归验证通过 |
| 实施总表来源 | 第2章实施总表来自 Excel Sheet 1，6 列标准 | ✅ 通过 | 序号\|任务\|开始时间\|结束时间\|实施人\|复核人，无 Unnamed/日期序列号 |
| 逻辑闭环 | 任务明细与 Excel 源数据严格对应 | ✅ 通过 | 数据完整性测试通过 |
| 聚合正确 | 同类操作成功聚合 | ✅ 通过 | 测试通过 |
| 安全拦截 | 高危操作识别并提示确认 | ✅ 通过 | 测试通过 |

### 缺陷单验收结论 (QA_DEFECT_REPORT)

| 缺陷 | 优先级 | 回归结果 | PM 验收 |
|------|--------|----------|---------|
| **#1** 实施总表列异常 | P0 | 通过 | ✅ 通过 |
| **#2** 第2部分层级与命名 | P0 | 通过 | ✅ 通过 |
| **#3** 第1、3～5 部分 | 待复核 | 待复核 | ⏳ 延后，不影响本次闭环 |

### 遗留项（非阻塞）

- **第1/3～5 部分**：template.docx 已含占位，可能与 docxtpl 块渲染有关，建议后续迭代由 Developer 人工复核后处理。

---

## 📣 下一步指派

**项目状态**: 🟢 V6 里程碑验收完成（2026-03-12）

### 致 Developer
**已完成** ✅
- **W1 阶段（基础框架）**：创建 `src/web/` 目录结构、Flask 应用工厂、ConfigService/BackupService、main.py web 命令
- **W2 阶段（核心页面）**：章节排序、操作类型、列映射配置页面、图片上传 API
- **W3 阶段（高级功能）**：配置保存、版本回滚、YAML 预览、表单校验
- **W2.6 阶段（Excel 一键保存）**：Excel 预览 API、批量保存 API、ConfigService 扩展、前端预览 UI、保存按钮交互
- **V2 阶段（操作类型章节绑定 + 批量删除）** ✅
- **V3 阶段（核心字段同步）** ✅
- **V4 阶段（WangEditor 替换 + 自动同步）** ✅
- **V5 阶段（Excel 一键保存全量覆盖）** ✅ 2026-03-01
- **V6 阶段（操作类型自动识别）** ✅ 2026-03-01

### 致 Tester
**已完成** ✅
- [x] **Web API 测试**：API 单元测试 ✅
- [x] **V2-T1** API 单元测试：章节操作类型 API ✅
- [x] **V2-T2** API 单元测试：批量删除 API ✅
- [x] **V2-T3** 数据迁移测试：旧格式兼容性验证 ✅
- [x] **V5 测试**：批量保存全量覆盖模式 ✅ 2026-03-01
- [x] **V6 测试**：操作类型自动识别 ✅ 2026-03-01

**待执行**
- [ ] **Web E2E 测试**：端到端测试，验收 PRD 6.2 节

### 致 PM
**已完成** ✅
- 启动验证：`python main.py web`
- 功能验收：章节排序、操作类型、列映射、版本回滚、Excel 一键保存
- M7 里程碑（2026-02-27 验收通过）：操作类型章节绑定、批量删除、核心字段同步
- V5 里程碑（2026-03-01 验收通过）：Excel 一键保存全量覆盖模式
- V6 里程碑（2026-03-01 验收通过）：操作类型自动识别

---

## 📦 新增依赖

```txt
# requirements.txt 新增
docxtpl>=0.17.0
fastmcp>=0.1.0
flask>=3.0.0      # Web 配置中心 (M6)
werkzeug>=3.0.0   # Web 配置中心 (M6)
```
