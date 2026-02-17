# OpsPilot - 运维副驾驶

自动化部署方案生成工具，通过解析规范化 Excel 清单（上线内容），自动输出符合样式的 Word 实施文档。

## 功能特性

- **智能解析**：支持多 Sheet 结构的 Excel 文件，自动提取任务名、操作类型、部署单元等核心字段
- **章节排序**：根据配置文件自动排序 Word 章节顺序，空数据自动跳过
- **任务聚合**：相同操作类型的任务自动合并处理，生成规范化表格
- **风险识别**：自动扫描并拦截删除、下线、重建等高危操作
- **人机协同**：两阶段执行模式，分析结果需人工确认后方可生成文档

## 安装

```bash
# 克隆项目
git clone <repository_url>
cd OpsPilot

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

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
# 跳过人工确认，直接执行完整流程（仅建议无高危操作时使用）
python main.py run <excel_file>

# 强制执行包含高危操作的流程
python main.py run <excel_file> --force
```

## 命令说明

| 命令 | 说明 |
|------|------|
| `analyze <excel_file>` | 分析阶段：解析 Excel，输出 report.json |
| `generate <report_file>` | 生成阶段：读取 report.json，输出 Word 文档 |
| `run <excel_file>` | 完整流程：分析 + 生成 |

### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出文件路径 | `output/实施文档.docx` |
| `-c, --config` | 规则配置文件路径 | `config/rules.yaml` |
| `-t, --template` | 模板文件路径 | `templates/实施文档.doc` |
| `-f, --force` | 跳过高危操作确认 | False |

## 目录结构

```
OpsPilot/
├── main.py                 # CLI 入口
├── config/
│   └── rules.yaml          # 业务规则配置（排序、映射）
├── templates/
│   └── 实施文档.doc         # Word 模板
├── src/
│   ├── parser/             # 解析模块
│   │   └── excel_parser.py
│   └── renderer/           # 渲染模块
│       └── word_renderer.py
├── output/                 # 输出目录
│   ├── report.json         # 中间态数据
│   └── 实施文档.docx        # 生成的文档
├── tests/                  # 测试用例
└── docs/
    ├── OpsPilot_PRD.md     # 产品需求文档
    └── PROJECT_PROGRESS.md # 项目进度
```

## 配置说明

业务规则通过 `config/rules.yaml` 配置，包括：

- **优先级 (Priority)**：定义各 Sheet 在 Word 章节中的先后顺序
- **动作映射 (Mapping)**：定义操作类型对应的详细步骤描述文本
- **高危操作**：定义需要人工确认的高危操作关键字

## 开发指南

### 环境准备

```bash
# 安装开发依赖
pip install -r requirements.txt
pip install pytest  # 测试框架
```

### 运行测试

```bash
pytest tests/
```

### 架构原则

1. **模块化解耦**：解析逻辑与文档渲染分离
2. **规则驱动**：业务逻辑从 `rules.yaml` 读取，禁止硬编码
3. **中间态协议**：解析层与渲染层通过 `report.json` 通信

## 许可证

MIT License
