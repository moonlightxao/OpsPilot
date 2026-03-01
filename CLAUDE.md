# OpsPilot 项目规则

## 项目简介

OpsPilot 是一个 Excel 清单到 Word 实施文档的自动化转换工具。

```
Excel 清单 → Parser 解析 → report.json → Renderer 渲染 → Word 实施文档
```

技术栈：Python 3.x + pandas + python-docx + docxtpl + Click + Flask + FastMCP

## 角色切换命令

使用斜杠命令切换角色（减少上下文占用）：

| 命令 | 角色 | 职责 |
|------|------|------|
| `/dev` | 开发工程师 | 逻辑编写、数据处理、渲染实现 |
| `/arch` | 架构师 | 架构设计、技术选型、接口规范 |
| `/test` | 测试人员 | 单元测试、集成测试、验收校验 |
| `/pm` | 产品经理 | 需求理解、PRD 细化、成果验收 |

## Git 提交规范

### 最小可提交单元（MCU）

每次完成以下任意一项工作，**必须立即提交并推送到远程仓库**：

| 单元类型 | 示例 |
|---|---|
| 单个函数/方法 | `parse_excel_header()`, `render_table()` |
| 单个测试用例 | `test_excel_parser.py` 中的一个 `test_xxx` |
| 单个配置修改 | `rules.yaml` 中新增一个映射规则 |
| 单个文档更新 | `PROJECT_PROGRESS.md` 中勾选任务完成 |
| 单个 Bug 修复 | 修复一个具体 issue |

### 提交信息格式

```
<type>(<scope>): <subject>

<body>
```

#### Type 类型

| 类型 | 说明 | 示例 |
|---|---|---|
| `feat` | 新功能 | `feat(parser): 新增 Excel 多 Sheet 解析` |
| `fix` | Bug 修复 | `fix(renderer): 修复表格边框渲染异常` |
| `refactor` | 重构（不改变功能） | `refactor(parser): 拆分解析逻辑为独立函数` |
| `test` | 测试相关 | `test(parser): 添加 parse_header 单元测试` |
| `docs` | 文档更新 | `docs: 更新 PROJECT_PROGRESS 进度` |
| `chore` | 构建/工具/配置 | `chore: 更新 requirements.txt` |

#### Scope 范围（按模块）

- `parser` - 解析模块（`src/parser/`）
- `renderer` - 渲染模块（`src/renderer/`）
- `config` - 配置文件（`config/`）
- `core` - 核心逻辑（`src/core/`）
- `cli` - 命令行接口
- `web` - Web 配置中心（`src/web/`）
- `mcp` - MCP 服务（`src/mcp/`）

#### Subject 主题

- 使用中文简明描述
- 不超过 50 字符
- 不以句号结尾
- 动词开头（新增、修复、更新、移除、重构）

### 禁止行为

- ❌ 累积多个功能后一次性提交
- ❌ 使用无意义提交信息（`update`, `fix bug`, `改动`）
- ❌ 提交与主体无关的文件
- ❌ 提交包含敏感信息的文件

### 提交流程

```bash
# 1. 查看变更
git status
git diff

# 2. 暂存变更（精确到文件）
git add <specific_files>

# 3. 提交（规范格式）
git commit -m "feat(parser): 新增 Excel 多 Sheet 解析"

# 4. 立即推送
git push origin <branch>
```

## 项目进展

项目执行看板位于 `docs/PROJECT_PROGRESS.md`。

- 完成任何任务后必须同步更新此文件
- 在变更日志中追加记录：`[日期] [角色] 动作 | 产出物`

## 核心目录结构

```
OpsPilot/
├── main.py                 # CLI 入口
├── src/
│   ├── parser/             # Excel 解析模块
│   ├── renderer/           # Word 渲染模块
│   ├── mcp/                # MCP 服务模块
│   └── web/                # Web 配置中心
├── config/
│   └── rules.yaml          # 业务规则配置（禁止硬编码）
├── templates/
│   └── template.docx       # Word 模板（Jinja2 占位符）
├── output/
│   └── report.json         # 中间态数据
├── docs/
│   ├── OpsPilot_PRD.md     # 产品需求文档
│   ├── PROJECT_PROGRESS.md # 项目进展看板
│   └── report_schema.md    # report.json 协议
└── tests/                  # 测试用例
```

## 常用命令

```bash
# 解析 Excel → report.json
python main.py analyze <excel_file> -o output/report.json -c config/rules.yaml

# 从 report.json 生成 Word
python main.py generate output/report.json -o output/实施文档.docx -t templates/template.docx

# 一键：解析 + 生成
python main.py run <excel_file>

# 启动 Web 配置中心
python main.py web

# MCP 服务
python -m src.mcp.server

# 测试
pytest tests/
```

## 关键原则

1. **规则驱动**：所有业务逻辑从 `config/rules.yaml` 读取，禁止在代码中硬编码
2. **两阶段执行**：analyze 与 generate 分离，强制人工确认环节
3. **高危拦截**：删除/下线/重建等操作触发挂起确认流程
4. **模板驱动**：使用 docxtpl 模板填充，确保视觉效果与样板一致
