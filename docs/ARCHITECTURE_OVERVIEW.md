# OpsPilot 项目架构概览

> 本文档供开发人员快速上手，描述代码结构、接口定义及潜在冗余。

---

## 1. 项目定位

OpsPilot 是一个自动化部署方案生成工具，核心流程：

```
Excel 清单 → Parser 解析 → report.json → Renderer 渲染 → Word 实施文档
```

**技术栈**：Python 3.x + pandas + python-docx + docxtpl + Click + FastMCP

---

## 2. 目录结构

```
OpsPilot/
├── main.py                      # CLI 入口（Click 框架）
├── config/
│   └── rules.yaml               # 业务规则配置（核心）
├── templates/
│   └── template.docx            # Word 模板（Jinja2 占位符）
├── src/
│   ├── parser/
│   │   ├── __init__.py          # 模块导出
│   │   └── excel_parser.py      # Excel 解析器（805 行）
│   ├── renderer/
│   │   ├── __init__.py          # 模块导出
│   │   └── template_renderer.py # Word 渲染器（460 行）
│   └── mcp/
│       ├── __init__.py
│       └── server.py            # MCP 服务（FastMCP）
├── tests/
│   ├── conftest.py              # pytest fixtures
│   ├── test_parser.py           # Parser 单元测试
│   ├── test_renderer.py         # Renderer 单元测试
│   ├── test_e2e.py              # 端到端测试
│   ├── test_mcp.py              # MCP 服务测试
│   └── ...                      # 其他测试
├── output/                      # 输出目录
│   ├── report.json              # 中间态数据
│   └── 实施文档.docx            # 生成文档
└── docs/
    ├── report_schema.md         # report.json 协议规范
    ├── OpsPilot_PRD.md          # 产品需求文档
    └── PROJECT_PROGRESS.md      # 项目进度
```

---

## 3. 核心模块详解

### 3.1 CLI 入口 - `main.py`

**职责**：命令行接口，协调 Parser 和 Renderer。

**命令**：

| 命令 | 功能 | 参数 |
|------|------|------|
| `analyze` | 解析 Excel，输出 report.json | `-o` 输出路径, `-c` 配置路径 |
| `generate` | 读取 report.json，输出 Word | `-o` 输出路径, `-t` 模板路径 |
| `run` | 完整流程（analyze + generate） | `-f` 强制执行高危操作 |

**关键函数**：

```python
def safe_echo(message: str, err: bool = False) -> None:
    """兼容 Windows GBK 控制台的安全输出"""

@cli.command()
def analyze(excel_file: str, output: str, config: str): ...
def generate(report_file: str, output: str, template: str, config: str): ...
def run(excel_file: str, output: str, config: str, force: bool): ...
```

---

### 3.2 解析模块 - `src/parser/excel_parser.py`

**职责**：读取多 Sheet Excel，动态表头解析，数据清洗，生成 `report.json`。

**核心类**：`ExcelParser`

**公开接口**：

```python
class ExcelParser:
    PROTOCOL_VERSION = "2.1.0"
    
    def __init__(self, config_path: str = "config/rules.yaml"): ...
    
    def parse(self, excel_path: str) -> dict:
        """
        解析 Excel 文件，返回 report.json 结构
        
        Args:
            excel_path: Excel 文件路径
        Returns:
            符合 docs/report_schema.md v2.1 规范的字典
        """
    
    def get_sheets(self) -> list[str]:
        """返回按优先级排序的 Sheet 名称列表"""
    
    def get_columns_for_sheet(self, sheet_name: str) -> list[str]:
        """获取指定 Sheet 的列配置"""
```

**便捷函数**：

```python
def parse_excel(excel_path: str, config_path: str = "config/rules.yaml") -> dict:
    """便捷函数，一键解析"""
```

**内部方法（关键）**：

| 方法 | 功能 |
|------|------|
| `_parse_implementation_summary()` | 解析第一个 Sheet 作为实施总表 |
| `_parse_sheet()` | 解析单个 Sheet |
| `_build_field_mapping()` | 动态表头映射（基于 core_fields 别名） |
| `_is_high_risk()` | 高危操作检测 |
| `_sanitize_string()` | 清理非法字符 |
| `_extract_cells_by_columns_with_mapping()` | 按列映射提取单元格 |

**异常类**：

```python
class ExcelParserError(Exception): ...
class SheetNotFoundError(ExcelParserError): ...
class RequiredFieldMissingError(ExcelParserError): ...
```

---

### 3.3 渲染模块 - `src/renderer/template_renderer.py`

**职责**：基于 `report.json` 生成 Word 文档，支持 docxtpl 模板和内置渲染两种模式。

**核心类**：`TemplateRenderer`

**公开接口**：

```python
class TemplateRenderer:
    def __init__(self, config_path: str = "config/rules.yaml"): ...
    
    def render(self, report: dict, template_path: str, output_path: str) -> str:
        """
        渲染 Word 文档
        
        Args:
            report: report.json 数据
            template_path: 模板路径（无模板时使用内置渲染）
            output_path: 输出路径
        Returns:
            实际输出的文件路径
        """
```

**便捷函数**：

```python
def render_with_template(
    report: dict,
    template_path: str = "templates/template.docx",
    output_path: str = "output/实施文档.docx",
    config_path: str = "config/rules.yaml"
) -> str: ...
```

**渲染策略**：

1. **模板渲染**（`_render_with_template`）：检测模板是否包含 Jinja2 标记
2. **内置渲染**（`_render_builtin`）：使用 python-docx 直接生成，5 章节结构

**Word 文档结构**：

1. 原因和目的
2. 实施步骤和计划（含实施总表 + 详细步骤）
3. 实施后验证计划
4. 应急回退措施
5. 风险分析和规避措施

---

### 3.4 MCP 服务 - `src/mcp/server.py`

**职责**：通过 MCP 协议暴露 OpsPilot 能力供外部 Agent 调用。

**工具列表**：

```python
@mcp.tool()
def opspilot_analyze(excel_path: str, config_path: str = "config/rules.yaml") -> dict:
    """解析 Excel，返回 report.json 结构化数据"""

@mcp.tool()
def opspilot_generate(
    report: dict,
    template_path: str = "templates/template.docx",
    output_path: str = "output/实施文档.docx",
    config_path: str = "config/rules.yaml"
) -> str:
    """基于 report 数据生成 Word"""

@mcp.tool()
def opspilot_run(
    excel_path: str,
    config_path: str = "config/rules.yaml",
    template_path: str = "templates/template.docx",
    output_path: str = "output/实施文档.docx",
    force: bool = False
) -> str:
    """完整流程：解析 + 生成"""
```

**启动方式**：

```bash
python -m src.mcp.server
```

---

## 4. 中间态协议 - `report.json`

**协议版本**：v2.1.0

**规范文档**：`docs/report_schema.md`

### 4.1 数据结构

```json
{
  "meta": {
    "source_file": "string",
    "generated_at": "ISO 8601",
    "version": "2.1.0"
  },
  "summary": {
    "total_tasks": "int",
    "total_sheets": "int",
    "high_risk_count": "int",
    "has_external_links": "bool",
    "external_links": ["string"]
  },
  "has_risk_alerts": "bool",
  "risk_alerts": [
    {
      "sheet_name": "string",
      "action_type": "string",
      "task_count": "int",
      "task_names": ["string"]
    }
  ],
  "implementation_summary": {
    "sheet_name": "string",
    "columns": ["序号", "任务", "开始时间", "结束时间", "实施人", "复核人"],
    "rows": [{ "cells": ["string"] }],
    "has_data": "bool"
  },
  "sections": [
    {
      "section_name": "string",
      "priority": "int",
      "has_action_groups": "bool",
      "columns": ["string"],
      "action_groups": [
        {
          "action_type": "string",
          "instruction": "string",
          "is_high_risk": "bool",
          "task_count": "int",
          "tasks": [{ "cells": ["string"] }]
        }
      ]
    }
  ]
}
```

### 4.2 关键字段说明

| 字段 | 用途 |
|------|------|
| `sections[].columns` | 定义表格表头，模板渲染时直接使用 |
| `tasks[].cells` | 按列顺序的单元格值数组，适配 Jinja2 循环 |
| `is_high_risk` | 高危标记，支持模板 `{% if %}` 条件渲染 |
| `implementation_summary` | v2.1 新增，第2章实施总表数据 |

---

## 5. 配置文件 - `config/rules.yaml`

**核心配置模块**：

| 模块 | 用途 |
|------|------|
| `implementation_summary` | 实施总表解析策略（Sheet 选择、列映射、日期转换） |
| `priority_rules` | 章节（Sheet）优先级，决定 Word 输出顺序 |
| `action_library` | 操作类型语义展开（instruction、is_high_risk） |
| `high_risk_keywords` | 高危操作关键字列表 |
| `sheet_column_mapping` | 不同 Sheet 的表格列定义与别名映射 |
| `core_fields` | 必须解析的核心字段（task_name、action_type 等） |
| `output_config` | Word 输出样式配置（字体、颜色等） |

---

## 6. 测试套件

| 文件 | 覆盖范围 |
|------|----------|
| `conftest.py` | 共享 fixtures（sample_config, sample_excel 等） |
| `test_parser.py` | Parser 单元测试（动态表头、高危检测、字段验证等） |
| `test_renderer.py` | Renderer 单元测试 |
| `test_e2e.py` | 端到端集成测试 |
| `test_mcp.py` | MCP 服务测试 |
| `test_golden_sample.py` | 黄金样本对比测试 |
| `test_template_comparison.py` | 模板对比测试 |

**运行测试**：

```bash
pytest tests/
```

---

## 7. 识别的冗余代码与建议

### 7.1 需删除的临时文件

| 文件/目录 | 类型 | 建议 |
|-----------|------|------|
| `fix_template.py` | 临时脚本 | 删除 |
| `fix_template_v2.py` | 临时脚本 | 删除 |
| `fix_template_v3.py` | 临时脚本 | 删除 |
| `replace_template.py` | 临时脚本 | 删除 |
| `scripts/create_template.py` | 临时脚本 | 评估后删除或移入 docs |
| `temp_docx_extract/` | 临时目录 | 删除 |

### 7.2 代码层面的冗余

#### 问题 1：`excel_parser.py` 中重复的方法

**位置**：`excel_parser.py` 第 678 行和第 778 行

```python
# 第 678 行（私有方法）
def _get_columns_for_sheet(self, sheet_name: str) -> list[str]: ...

# 第 778 行（公开方法）
def get_columns_for_sheet(self, sheet_name: str) -> list[str]:
    return self._get_columns_for_sheet(sheet_name)
```

**建议**：保留公开方法，删除私有方法并直接实现逻辑，或保留私有方法但删除公开方法中的简单转发。

#### 问题 2：废弃的 `output/` 文件

| 文件 | 说明 | 建议 |
|------|------|------|
| `output/实施文档.json` | 测试输出 | 添加到 .gitignore |
| `output/实施文档_builtin.docx` | 测试输出 | 添加到 .gitignore |
| `output/瀹炴柦鏂囨。.json` | 编码错误的测试文件 | 删除 |
| `output/瀹炴柦鏂囨。.docx` | 编码错误的测试文件 | 删除 |

#### 问题 3：`templates/` 目录冗余文件

| 文件 | 说明 | 建议 |
|------|------|------|
| `templates/~$mplate.docx` | Word 临时文件 | 删除，添加到 .gitignore |
| `templates/template.docx.bak` | 备份文件 | 评估后删除 |
| `templates/template_broken.docx` | 损坏模板 | 删除 |
| `templates/template_fixed.docx` | 修复版模板 | 合并到 template.docx 后删除 |
| `templates/template_fixed_v2.docx` | 修复版模板 | 同上 |
| `templates/template_new.docx.bak` | 备份文件 | 删除 |

### 7.3 建议的 .gitignore 补充

```gitignore
# 输出文件
output/*.json
output/*.docx

# Word 临时文件
templates/~$*.docx

# Python 缓存
__pycache__/
*.pyc
src/**/__pycache__/

# 临时目录
temp_docx_extract/
```

---

## 8. 快速上手流程

### 8.1 开发环境

```bash
# 1. 克隆项目
git clone <repo_url>
cd OpsPilot

# 2. 创建虚拟环境
python -m venv .venv
.\\.venv\\Scripts\\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行测试
pytest tests/
```

### 8.2 调试流程

```bash
# 解析阶段
python main.py analyze docs/Sample_Files/上线checklist.xlsx

# 查看中间结果
cat output/report.json

# 生成阶段
python main.py generate output/report.json

# 或完整流程
python main.py run docs/Sample_Files/上线checklist.xlsx
```

### 8.3 扩展开发

**新增 Sheet 类型**：
1. 在 `config/rules.yaml` 的 `priority_rules` 添加优先级
2. 在 `sheet_column_mapping` 添加列定义
3. 运行测试验证

**新增操作类型**：
1. 在 `config/rules.yaml` 的 `action_library` 添加定义
2. 如需高危检测，添加到 `high_risk_keywords`

**修改 Word 输出**：
- 修改 `templates/template.docx`（推荐）
- 或修改 `template_renderer.py` 的 `_render_builtin` 方法

---

## 9. 架构原则（提醒）

1. **模块化解耦**：Parser 和 Renderer 通过 `report.json` 通信，互不直接依赖
2. **规则驱动**：所有业务逻辑从 `rules.yaml` 读取，禁止硬编码
3. **防御性编程**：处理空值、非法字符、缺失字段
4. **两阶段执行**：分析 → 人工确认 → 生成

---

*文档版本：2026-02-25*
*维护者：架构师*
