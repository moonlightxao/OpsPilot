# 技术方案：双轨渲染架构设计

## 1. 背景与目标

### 1.1 问题分析
当前 `TemplateRenderer` 中的 `_render_builtin()` 方法将文档结构硬编码在代码中，存在以下问题：
- **扩展性差**：新增章节/样式需修改源代码
- **维护成本高**：业务变更需开发者介入
- **非技术人员无法定制**：无法通过配置文件调整输出格式

### 1.2 目标
实现**双轨渲染架构**：
1. **保留内置渲染**：作为兜底方案，无模板时自动回退
2. **支持模板渲染**：用户可通过 `templates/` 下的 `.docx` 模板定制输出
3. **配置驱动切换**：通过 `rules.yaml` 控制渲染策略

---

## 2. 架构设计

### 2.1 渲染策略枚举

```python
class RenderStrategy(Enum):
    AUTO = "auto"        # 优先模板，失败则内置
    TEMPLATE = "template"  # 仅使用模板
    BUILTIN = "builtin"    # 仅使用内置渲染
```

### 2.2 配置扩展（rules.yaml）

```yaml
# 渲染策略配置
render_config:
  strategy: "auto"           # auto | template | builtin
  template_path: "templates/template.docx"
  fallback_to_builtin: true   # 模板渲染失败时是否回退
  template_required: false    # template 策略下模板是否必需
```

### 2.3 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    TemplateRenderer                          │
├─────────────────────────────────────────────────────────────┤
│  render(report, template_path, output_path)                 │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────────┐                                        │
│  │  策略判断        │ ← rules.yaml → render_config.strategy │
│  └────────┬────────┘                                        │
│           │                                                  │
│     ┌─────┴─────┬──────────────┐                            │
│     ▼           ▼              ▼                            │
│  ┌──────┐  ┌──────────┐  ┌──────────┐                      │
│  │ AUTO │  │ TEMPLATE │  │ BUILTIN  │                      │
│  └──┬───┘  └────┬─────┘  └────┬─────┘                      │
│     │           │              │                            │
│     ▼           ▼              ▼                            │
│  ┌────────────────────────────────────────┐                │
│  │  _render_with_template()  ← docxtpl   │                │
│  │  _render_builtin()        ← python-docx│                │
│  └────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 模板规范

### 3.1 Jinja2 语法支持

模板文件 `templates/template.docx` 使用 docxtpl 兼容的 Jinja2 语法：

```jinja2
{# 文档标题 #}
{{ title }}

{# 第1部分：原因和目的 #}
1 原因和目的

1.1 变更应用
{{ meta.application_name | default('（待填写）') }}

1.2 变更原因和目的
{{ meta.change_reason | default('（待填写）') }}

{# 摘要信息 #}
【摘要信息】
• 任务总数：{{ summary.total_tasks }}
• 涉及模块：{{ summary.total_sheets }} 个
• 高危操作：{{ summary.high_risk_count }} 个

{# 实施总表 #}
{% if implementation_summary.has_data %}
2 实施步骤和计划
{% for row in implementation_summary.rows %}
{% for cell in row.cells %}{{ cell }}{% endfor %}
{% endfor %}
{% endif %}

{# 风险告警 #}
{% if has_risk_alerts %}
⚠️ 高危操作告警
{% for alert in risk_alerts %}
【{{ alert.sheet_name }}】{{ alert.action_type }} - 共 {{ alert.task_count }} 个任务
{% for task_name in alert.task_names %}
  • {{ task_name }}
{% endfor %}
{% endfor %}
{% endif %}

{# 章节循环 #}
{% for section in sections | sort(attribute='priority') %}
{{ section.section_name }}
{% for action_group in section.action_groups %}
{% if action_group.is_high_risk %}⚠️ {% endif %}{{ action_group.action_type }}
{{ action_group.instruction }}

{# 任务表格 #}
{% for task in action_group.tasks %}
{% for cell in task.cells %}{{ cell }}{% endfor %}
{% endfor %}
{% endfor %}
{% endfor %}
```

### 3.2 模板文件目录结构

```
templates/
├── template.docx          # 默认模板（docxtpl 格式）
├── template_builtin.docx  # 样式参考（纯样式，无 Jinja）
└── custom/                # 自定义模板目录
    └── *.docx
```

---

## 4. 代码变更

### 4.1 TemplateRenderer 类变更

**文件**: `src/renderer/template_renderer.py`

#### 新增方法

```python
from enum import Enum

class RenderStrategy(Enum):
    AUTO = "auto"
    TEMPLATE = "template"
    BUILTIN = "builtin"

class TemplateRenderer:
    def __init__(self, config_path: str = "config/rules.yaml"):
        # ... 现有代码 ...
        self._render_config = self._config.get('render_config', {})
    
    def render(self, report: dict, template_path: str, output_path: str) -> str:
        strategy = self._get_render_strategy()
        
        if strategy == RenderStrategy.BUILTIN:
            return self._render_builtin(report, output_path)
        
        if strategy == RenderStrategy.TEMPLATE:
            return self._render_with_template_strict(report, template_path, output_path)
        
        # AUTO: 优先模板，失败回退
        return self._render_auto(report, template_path, output_path)
    
    def _get_render_strategy(self) -> RenderStrategy:
        strategy_str = self._render_config.get('strategy', 'auto')
        return RenderStrategy(strategy_str)
    
    def _render_auto(self, report: dict, template_path: str, output_path: str) -> str:
        """AUTO 策略：优先模板，失败回退内置"""
        template_file = Path(template_path)
        if template_file.exists() and self._is_docxtpl_template(template_file):
            try:
                return self._render_with_template(report, template_file, output_path)
            except Exception:
                if self._render_config.get('fallback_to_builtin', True):
                    return self._render_builtin(report, output_path)
                raise
        return self._render_builtin(report, output_path)
    
    def _render_with_template_strict(
        self, report: dict, template_path: str, output_path: str
    ) -> str:
        """TEMPLATE 策略：严格使用模板，不回退"""
        template_file = Path(template_path)
        if not template_file.exists():
            raise TemplateNotFoundError(f"模板文件不存在: {template_path}")
        return self._render_with_template(report, template_file, output_path)
```

### 4.2 配置文件变更

**文件**: `config/rules.yaml`

```yaml
# 渲染策略配置（新增）
render_config:
  strategy: "auto"              # auto | template | builtin
  template_path: "templates/template.docx"
  fallback_to_builtin: true     # AUTO 策略下模板失败是否回退
  template_required: false      # TEMPLATE 策略下模板是否必需
```

### 4.3 测试用例变更

**文件**: `tests/test_renderer.py`

新增测试类：
- `TestRenderStrategy` - 测试三种策略切换
- `TestTemplateNotFound` - 测试模板不存在时的行为
- `TestFallbackBehavior` - 测试回退机制

---

## 5. 实现清单

| 序号 | 任务 | 负责人 | 产出物 |
|------|------|--------|--------|
| 1 | 新增 `RenderStrategy` 枚举 | Developer | `template_renderer.py` |
| 2 | 实现 `_get_render_strategy()` | Developer | `template_renderer.py` |
| 3 | 实现 `_render_auto()` | Developer | `template_renderer.py` |
| 4 | 实现 `_render_with_template_strict()` | Developer | `template_renderer.py` |
| 5 | 重构 `render()` 方法 | Developer | `template_renderer.py` |
| 6 | 扩展 `rules.yaml` 配置 | Architect | `config/rules.yaml` |
| 7 | 更新文档 | Architect | `report_schema.md` |
| 8 | 新增策略测试用例 | Tester | `test_renderer.py` |
| 9 | 回归测试 | Tester | 测试报告 |

---

## 6. 使用示例

### 6.1 AUTO 策略（默认）

```python
renderer = TemplateRenderer()
# 优先使用模板，模板不存在或渲染失败时回退内置
renderer.render(report, "templates/template.docx", "output/result.docx")
```

### 6.2 TEMPLATE 策略

```yaml
# config/rules.yaml
render_config:
  strategy: "template"
```

```python
renderer = TemplateRenderer()
# 严格使用模板，失败抛出异常
renderer.render(report, "templates/custom/my_template.docx", "output/result.docx")
```

### 6.3 BUILTIN 策略

```yaml
# config/rules.yaml
render_config:
  strategy: "builtin"
```

```python
renderer = TemplateRenderer()
# 仅使用内置渲染，忽略模板参数
renderer.render(report, "", "output/result.docx")
```

---

## 7. 兼容性说明

| 场景 | 原行为 | 新行为 |
|------|--------|--------|
| 无模板文件 | 内置渲染 | 内置渲染（策略 AUTO） |
| 有 docxtpl 模板 | 模板渲染 | 模板渲染（策略 AUTO） |
| 模板渲染失败 | 回退内置 | 取决于 `fallback_to_builtin` |
| 模板无 Jinja 标记 | 内置渲染 | 内置渲染（检测为非模板） |

---

## 8. 风险评估

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| 策略配置错误 | 低 | 枚举值校验 + 默认 AUTO |
| 模板语法错误 | 中 | 捕获 Jinja2 异常，回退内置 |
| 配置迁移 | 低 | 向后兼容，默认 AUTO 策略 |

---

## 9. 验收标准

1. **功能验收**
   - [ ] AUTO 策略：模板存在时使用模板，不存在时使用内置
   - [ ] TEMPLATE 策略：严格使用模板，失败抛出 `TemplateNotFoundError`
   - [ ] BUILTIN 策略：忽略模板，直接使用内置渲染

2. **兼容性验收**
   - [ ] 现有测试全部通过
   - [ ] 无模板时行为与原实现一致
   - [ ] 黄金样本端到端测试通过

3. **配置验收**
   - [ ] `rules.yaml` 新增 `render_config` 节点
   - [ ] 策略值校验（仅允许 auto/template/builtin）

---

**文档版本**: v1.0
**创建日期**: 2026-02-25
**作者**: Architect
