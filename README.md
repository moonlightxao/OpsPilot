# OpsPilot - 运维副驾驶

自动化部署方案生成工具，通过解析规范化 Excel 清单（上线内容），自动输出符合样式的 Word 实施文档。

**技术选型**：核心转换引擎 Python，渲染引擎 `docxtpl`（Jinja2），Web 框架 Flask。

## 功能特性

- **智能解析**：支持多 Sheet 结构的 Excel 文件，自动提取任务名、操作类型、部署单元等核心字段
- **模板渲染**：基于 `docxtpl` + Jinja2 模板驱动，确保输出样式与样板一致
- **章节排序**：根据 `rules.yaml` 自动排序 Word 章节顺序，空数据自动跳过
- **任务聚合**：相同操作类型的任务自动合并处理，生成规范化表格
- **风险识别**：自动扫描并拦截删除、下线、重建等高危操作
- **人机协同**：两阶段执行模式，分析结果需人工确认后方可生成文档
- **MCP 服务化**：支持通过 MCP 协议对外暴露工具，供外部 Agent 调用
- **Web 配置中心**：可视化界面管理规则配置，支持拖拽排序、富文本编辑、版本回滚

## 安装

```bash
# 克隆项目
git clone <repository_url>
cd OpsPilot

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 本地启动 & 测试速查

```bash
# 1. 创建并激活虚拟环境（可选但推荐）
python -m venv .venv
.\.venv\Scripts\activate  # Windows PowerShell

# 2. 安装依赖
pip install -r requirements.txt

# 3. 使用示例 Excel 一键跑通完整流程（生成实施文档）
python main.py run docs/Sample_Files/上线checklist.xlsx -o output/实施文档.docx

# 4. 查看生成结果：output/实施文档.docx 与 docs/Sample_Files/实施文档.docx 对比

# 5. 本地运行测试
pytest tests/
```

### 两阶段执行（推荐）

```bash
# 阶段 1: 分析 - 解析 Excel，生成 report.json
python main.py analyze <excel_file>

# 查看分析结果，确认无风险后执行阶段 2
# 阶段 2: 生成 - 渲染 Word 实施文档
python main.py generate output/report.json
```

### 完整流程

```bash
# 跳过人工确认，直接执行完整流程
python main.py run <excel_file>

# 强制执行包含高危操作的流程
python main.py run <excel_file> --force
```

### Web 配置中心

```bash
# 启动 Web 配置中心
python main.py web

# 访问 http://127.0.0.1:5000 进行可视化配置
```

## 命令说明

| 命令 | 说明 |
|------|------|
| `analyze <excel_file>` | 分析阶段：解析 Excel，输出 report.json |
| `generate <report_file>` | 生成阶段：读取 report.json，输出 Word 文档 |
| `run <excel_file>` | 完整流程：分析 + 生成 |
| `web` | 启动 Web 配置中心 |

### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出文件路径 | `output/实施文档.docx` |
| `-c, --config` | 规则配置文件路径 | `config/rules.yaml` |
| `-t, --template` | 模板文件路径（generate 命令） | `templates/template.docx` |
| `-f, --force` | 跳过高危操作确认 | False |

## 目录结构

```
OpsPilot/
├── main.py                     # CLI 入口
├── config/
│   ├── rules.yaml              # 业务规则配置（排序、映射、渲染策略）
│   ├── images/                 # 操作类型图片存储
│   └── backups/                # 配置备份目录
├── templates/
│   ├── template.docx           # Word 模板（Jinja2 占位符）
│   └── custom/                 # 自定义模板目录
├── src/
│   ├── parser/                 # 解析模块
│   │   ├── __init__.py
│   │   └── excel_parser.py
│   ├── renderer/               # 渲染模块
│   │   ├── __init__.py
│   │   └── template_renderer.py
│   ├── mcp/                    # MCP 服务层
│   │   ├── __init__.py
│   │   └── server.py
│   └── web/                    # Web 配置中心
│       ├── __init__.py
│       ├── app.py              # Flask 应用工厂
│       ├── routes/             # 路由模块
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── backup.py
│       │   └── upload.py
│       └── services/           # 服务层
│           ├── __init__.py
│           ├── config_service.py
│           └── backup_service.py
├── output/                     # 输出目录
│   ├── report.json             # 中间态数据（report.json v2.1）
│   └── 实施文档.docx           # 生成的文档
├── tests/                      # 测试用例
└── docs/
    ├── OpsPilot_PRD.md         # 产品需求文档
    ├── PROJECT_PROGRESS.md     # 项目进度
    ├── TECH_DESIGN_*.md        # 技术方案文档
    └── Sample_Files/           # 样例文件
```

## Web 配置中心

运维人员可通过 Web 界面可视化配置规则，无需直接编辑 YAML 文件。

### 核心功能

| 功能 | 说明 |
|------|------|
| **章节排序** | 拖拽调整 Excel Sheet → Word 章节的映射顺序 |
| **操作类型** | 表格化管理操作类型，支持富文本描述 + 图片上传 |
| **列映射** | 手动输入或 Excel 辅助识别列名别名 |
| **版本回滚** | 保留最近 10 个版本，支持一键回滚 |
| **YAML 预览** | 实时预览配置文件内容 |

### 使用方式

```bash
# 启动服务
python main.py web

# 浏览器访问
http://127.0.0.1:5000
```

### 配置存储

- 配置文件：`config/rules.yaml`
- 图片存储：`config/images/`
- 备份文件：`config/backups/rules.yaml.bak.{timestamp}`

## MCP 服务化

外部 Agent 可通过 MCP 协议调用 OpsPilot 能力。在 Cursor 等支持 MCP 的 IDE 中配置：

```json
{
  "mcpServers": {
    "opspilot": {
      "command": "python",
      "args": ["-m", "src.mcp.server"],
      "cwd": "<OpsPilot 项目根目录>"
    }
  }
}
```

**可用工具**：

| 工具名称 | 功能 |
|---------|------|
| `opspilot_analyze` | 解析 Excel，返回 report.json 结构化数据 |
| `opspilot_generate` | 基于 report 数据生成 Word 实施文档 |
| `opspilot_run` | 完整流程：解析 + 生成一体化 |

## 配置说明

业务规则通过 `config/rules.yaml` 配置，包括：

- **实施总表配置 (implementation_summary)**：定义第2章实施总表的来源 Sheet、列映射、日期转换
- **渲染策略 (render_config)**：控制渲染模式、模板路径、回退行为
- **优先级 (priority_rules)**：定义各 Sheet 在 Word 章节中的先后顺序
- **动作映射 (action_library)**：定义操作类型对应的详细步骤描述文本
- **高危操作 (high_risk_keywords)**：定义需要人工确认的高危操作关键字
- **列映射 (sheet_column_mapping)**：定义不同 Sheet 类型在 Word 表格中的列展示

## 开发指南

### 环境准备

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
pytest tests/
```

### 架构原则

1. **模块化解耦**：坚持将「分析逻辑」与「文档渲染」分离，支持异步人工确认流程
2. **规则驱动**：所有业务逻辑（排序、映射、渲染策略）必须从 `rules.yaml` 读取，禁止在代码中硬编码
3. **模板驱动**：使用 docxtpl 模板填充，确保视觉效果与样板一致
4. **中间态协议**：解析层与渲染层通过 `report.json` 通信，确保字段能被 LLM 清晰理解
5. **目录规范**：维护 `src/`、`config/`、`templates/`、`output/` 等目录的整洁与逻辑一致性

### 数据流向

```
Excel → Parser → report.json v2.1 (人工确认) → docxtpl → template.docx → Word 实施文档
  │                                                              ↑
  └────────────── MCP Server (opspilot_analyze/generate) ────────┘
```

### 项目进度

任务拆解与架构决策详见 `docs/PROJECT_PROGRESS.md`。

## 里程碑

| 里程碑 | 说明 | 状态 |
|--------|------|------|
| M1 | 跑通数据解析到 JSON 的全流程 | ✅ 完成 |
| M3 | 产出第一份完全符合样式的 Word 实施方案 | ✅ 完成 |
| M4 | 模板填充方案验证通过 | ✅ 完成 |
| M5 | MCP 服务上线，外部 Agent 可调用 | ✅ 完成 |
| M6 | Web 配置中心上线，可视化配置管理 | ✅ 完成 |

## 依赖

```txt
openpyxl>=3.1.0
python-docx>=0.8.11
docxtpl>=0.17.0
click>=8.0.0
pyyaml>=6.0
fastmcp>=0.1.0
flask>=3.0.0
werkzeug>=3.0.0
```

## 许可证

MIT License
