# 🚀 OpsPilot 项目执行看板

## 📊 总体进度状态
- **当前阶段**: MCP 服务化扩展
- **完成度**: [▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░] 85%
- **项目健康度**: 🟢 架构扩展中
- **更新日期**: 2026-02-22

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

## 🚩 风险与阻塞 (Risks & Blockers)
| 等级 | 类型 | 描述 | 状态 | 处理人 |
| :--- | :--- | :--- | :--- | :--- |
| 🟡 | 架构调整 | Renderer 模块需重写为 docxtpl 版本 | 进行中 | Developer |
| 🟡 | 新功能 | MCP Server 模块待开发 | 待开始 | Developer |
| 🟢 | 逻辑风险 | 非标准换行已在 `_sanitize_string` 中处理 | 已解决 | Developer |
| 🟢 | 代码规范 | `src/parser/__init__.py` 模块导出已修复 | 已解决 | Developer |
| 🟢 | 编码问题 | Windows 控制台 GBK 无法显示 emoji，已添加 safe_echo 函数处理 | 已解决 | Developer |

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
- [x] ~~**Word 渲染器 (Renderer)**：基于 `python-docx` 的表格与样式实现~~ ❌ 已废弃 2026-02-22
- [x] **模板文件创建**：创建 `templates/template.docx` 包含 Jinja2 占位符 ✅ 2026-02-22
- [ ] **模板渲染器开发**：基于 `docxtpl` 实现模板填充 ⏳ 进行中
- [ ] **Parser 适配 v2.0**：修改 report.json 输出格式适配新协议 ⏳ 待开始

### 2.5 MCP 服务化扩展 (Owner: Developer) 🆕
- [ ] **MCP 依赖安装**：`requirements.txt` 添加 `fastmcp>=0.1.0` ⏳ 待开始
- [ ] **MCP 目录创建**：创建 `src/mcp/` 目录及 `__init__.py` ⏳ 待开始
- [ ] **MCP Server 实现**：`src/mcp/server.py` 实现 3 个 MCP Tool ⏳ 待开始
- [ ] **Tool: opspilot_analyze**：封装 ExcelParser.parse() 为 MCP Tool ⏳ 待开始
- [ ] **Tool: opspilot_generate**：封装 Renderer.render() 为 MCP Tool ⏳ 待开始
- [ ] **Tool: opspilot_run**：实现完整流程的 MCP Tool ⏳ 待开始
- [ ] **MCP 启动入口**：支持 `python -m src.mcp.server` 启动 ⏳ 待开始

### 3. 质量保障 (Owner: Tester)
- [x] **单元测试**：Parser 29/30 通过，Renderer 22/22 全部通过 ✅ 2026-02-18
- [x] **边界测试**：空文件、缺失字段、非法字符处理已覆盖 ✅ 2026-02-18
- [x] **高危流程测试**：高危操作检测逻辑已验证（删除/下线正确标记） ✅ 2026-02-18
- [x] **端到端测试**：9/10 通过，编码问题已修复 ✅ 2026-02-18
- [x] **样式比对**：数据完整性、文档结构、格式检查全部通过 ✅ 2026-02-18
- [ ] **模板渲染测试**：验证 docxtpl 方案的输出与样板一致性 ⏳ 待开始
- [ ] **MCP 集成测试**：验证外部 Agent 可通过 MCP 正常调用 ⏳ 待开始

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

---

## 📋 架构设计摘要

### 模块边界
```
┌─────────────────────────────────────────────────────────────────────────┐
│                            OpsPilot                                      │
├─────────────┬─────────────┬─────────────┬─────────────────┬─────────────┤
│   Parser    │  Aggregator │  SafeGuard  │    Renderer     │  MCP Server │
│  (解析层)   │  (聚合层)   │  (安全层)   │    (渲染层)     │  (服务层)   │
│   ✅ 完成   │  ✅ 已合并   │ ✅ 已合并   │   🔄 重构中     │  🆕 待开发  │
├─────────────┴─────────────┴─────────────┴─────────────────┴─────────────┤
│                    report.json v2.0 (模板适配)                           │
├─────────────────────────────────────────────────────────────────────────┤
│                  templates/template.docx (Jinja2 模板)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                      config/rules.yaml (规则库)                         │
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
- [x] **M3**: 产出第一份完全符合样式的 Word 实施方案（成果对齐）✅ 2026-02-18
- [ ] **M4**: 模板填充方案验证通过（架构升级）⏳ 进行中
- [ ] **M5**: MCP 服务上线，外部 Agent 可调用（服务化）🆕 待开始

---

## 📣 下一步指派

**项目状态**: 🔄 架构扩展中

### 致 Developer

#### 优先级 P0（阻塞项）
1. 安装 `docxtpl` 依赖
2. 开发新的模板渲染器 `src/renderer/template_renderer.py`
3. 修改 Parser 输出格式适配 report.json v2.0

#### 优先级 P1（MCP 服务化）🆕
1. **安装 FastMCP**：`pip install fastmcp`，更新 `requirements.txt`
2. **创建 MCP 目录**：`src/mcp/__init__.py` 和 `src/mcp/server.py`
3. **实现 MCP Tool**：
   - `opspilot_analyze(excel_path, config_path?) -> dict`
   - `opspilot_generate(report, template_path, output_path) -> str`
   - `opspilot_run(excel_path, force?) -> str`
4. **启动入口**：确保 `python -m src.mcp.server` 可正常启动

#### MCP Server 接口规范 (Stub)

```python
# src/mcp/server.py - 接口 Stub
from fastmcp import FastMCP
from pathlib import Path

mcp = FastMCP("OpsPilot")

@mcp.tool()
def opspilot_analyze(excel_path: str, config_path: str = "config/rules.yaml") -> dict:
    """
    解析 Excel 文件，生成结构化分析数据
    
    Args:
        excel_path: Excel 文件路径（绝对路径或相对于项目根目录）
        config_path: 规则配置文件路径，默认 config/rules.yaml
    
    Returns:
        report.json 结构化数据（符合 docs/report_schema.md v2.0 规范）
    """
    # TODO: 调用 ExcelParser.parse()
    pass

@mcp.tool()
def opspilot_generate(
    report: dict, 
    template_path: str = "templates/实施文档.doc",
    output_path: str = "output/实施文档.docx"
) -> str:
    """
    基于分析数据生成 Word 实施文档
    
    Args:
        report: report.json 结构化数据
        template_path: Word 模板文件路径
        output_path: 输出文件路径
    
    Returns:
        生成的 Word 文件绝对路径
    """
    # TODO: 调用 TemplateRenderer.render()
    pass

@mcp.tool()
def opspilot_run(
    excel_path: str, 
    config_path: str = "config/rules.yaml",
    force: bool = False
) -> str:
    """
    完整流程：解析 Excel 并生成 Word 文档
    
    Args:
        excel_path: Excel 文件路径
        config_path: 规则配置文件路径
        force: 是否跳过高危操作确认
    
    Returns:
        生成的 Word 文件绝对路径
    """
    # TODO: 组合调用 analyze + generate
    pass

if __name__ == "__main__":
    mcp.run()
```

### 致 Tester
- 等待模板渲染器完成后，执行样式比对测试验证新方案
- 等待 MCP Server 完成后，编写 MCP 集成测试用例

---

## 📦 新增依赖

```txt
# requirements.txt 新增
docxtpl>=0.17.0
fastmcp>=0.1.0
```
