# -*- coding: utf-8 -*-
"""
Excel Parser Module
负责多 Sheet Excel 读取与动态表头解析

设计原则:
1. 防御性编程：处理空值、非法字符及缺失 Sheet 的边界情况
2. 动态表头：基于 rules.yaml 中的 core_fields 别名匹配
3. 可读性：复杂聚合环节附带详细注释
"""

import re
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import yaml
from openpyxl import load_workbook

# 抑制 openpyxl 的 DataValidation 警告
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def _excel_serial_to_date(val: Any) -> str:
    """
    Excel 日期序列号转 YYYY-MM-DD。
    1900-01-01 为 1，46315 约为 2026-10-xx。
    """
    if val is None:
        return ""
    if isinstance(val, (int, float)) and val > 0 and val < 2958466:
        base = datetime(1899, 12, 30)  # Excel 基准
        d = base + timedelta(days=int(val))
        return d.strftime("%Y-%m-%d")
    return str(val).strip()


def _is_excel_serial_column(col: str) -> bool:
    """
    判断列名是否为 Excel 日期序列号（误作为列名）。
    当 Excel 表头行某单元格为日期时，pandas 可能读出为 46315 等数字字符串。
    """
    s = str(col).strip()
    if not s or not s.isdigit():
        return False
    try:
        n = int(s)
        return 1 <= n < 2958466
    except ValueError:
        return False


class ExcelParserError(Exception):
    """Excel 解析异常基类"""
    pass


class SheetNotFoundError(ExcelParserError):
    """Sheet 不存在异常"""
    pass


class RequiredFieldMissingError(ExcelParserError):
    """必填字段缺失异常"""
    pass


class ExcelParser:
    """
    Excel 解析器
    
    职责：
    - 读取多 Sheet Excel 文件
    - 动态表头解析（基于 core_fields 配置的别名匹配）
    - 数据清洗与空值处理
    - 生成符合 report_schema.md 的中间态数据
    """
    
    # 协议版本号
    PROTOCOL_VERSION = "2.1.0"
    
    # 非法字符正则（控制字符和不可见字符）
    ILLEGAL_CHAR_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]')
    
    def __init__(self, config_path: str = "config/rules.yaml"):
        """
        初始化解析器
        
        Args:
            config_path: 规则配置文件路径
        """
        self.config_path = Path(config_path)
        self._config: dict = {}
        self._core_fields: dict = {}
        self._priority_rules: dict = {}
        self._action_library: dict = {}
        self._high_risk_keywords: list = []
        self._sheet_column_mapping: dict = {}
        self._default_columns: list = []

        # Sheet 分组正则：匹配 Name(subtitle) 格式
        self._parenthesis_pattern = re.compile(r'^(.+?)\(([^)]+)\)$')

        self._load_config()
    
    def _load_config(self) -> None:
        """加载并解析规则配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # 提取各配置模块
        self._core_fields = self._config.get('core_fields', {})
        self._priority_rules = self._config.get('priority_rules', {})
        self._action_library = self._config.get('action_library', {})
        self._high_risk_keywords = self._config.get('high_risk_keywords', [])
        self._sheet_column_mapping = self._config.get('sheet_column_mapping', {})
        self._default_columns = self._config.get('default_columns', [])
        self._implementation_summary_config = self._config.get('implementation_summary', {})

    def _parse_sheet_name_for_grouping(self, sheet_name: str) -> tuple[str, Optional[str]]:
        """
        解析 Sheet 名称，提取分组名和子标题。

        Args:
            sheet_name: 原始 Sheet 名称

        Returns:
            (group_name, sub_title) - 无括号时 sub_title 为 None

        Examples:
            >>> _parse_sheet_name_for_grouping('HIS-A-B(test1)')
            ('HIS-A-B', 'test1')
            >>> _parse_sheet_name_for_grouping('HIS-A-B')
            ('HIS-A-B', None)
        """
        match = self._parenthesis_pattern.match(sheet_name)
        if match:
            group_name = match.group(1).strip()
            sub_title = match.group(2)  # 保留原始格式，不做 strip
            return group_name, sub_title
        return sheet_name, None
    
    def get_sheets(self) -> list[str]:
        """
        获取所有已解析的 Sheet 名称列表
        
        Returns:
            Sheet 名称列表（按优先级排序）
        """
        # 返回优先级规则中定义的 Sheet，按优先级排序
        sorted_sheets = sorted(
            self._priority_rules.keys(),
            key=lambda x: self._priority_rules.get(x, 999)
        )
        return sorted_sheets
    
    def parse(self, excel_path: str) -> dict:
        """
        解析 Excel 文件，生成符合 report_schema.md 的中间态数据
        
        Args:
            excel_path: Excel 文件路径
            
        Returns:
            符合 report_schema.md 规范的字典数据
        """
        excel_file = Path(excel_path)
        if not excel_file.exists():
            raise FileNotFoundError(f"Excel 文件不存在: {excel_path}")
        
        # 使用 openpyxl 获取所有 Sheet 名称
        workbook = load_workbook(excel_file, read_only=True, data_only=True)
        available_sheets = workbook.sheetnames
        workbook.close()
        
        # 【实施总表】从「变更安排」Sheet 解析 implementation_summary
        implementation_summary = self._parse_implementation_summary(
            excel_file, available_sheets
        )
        
        # 确定实施总表使用的 Sheet 名称，该 Sheet 不进入 sections
        impl_summary_sheet_name = implementation_summary.get('sheet_name', '')
        
        # 解析结果容器
        sections = []
        all_external_links = []
        risk_alerts = []
        total_tasks = 0
        high_risk_count = 0
        
        # 过滤规则：只处理名称包含 "HIS"（忽略大小写）的 sheet
        # 「变更安排」已作为实施总表处理，不进入 sections
        sheets_to_process = [
            sheet for sheet in available_sheets
            if "HIS" in sheet.upper() and sheet != impl_summary_sheet_name
        ]

        # 构建 Sheet 名称到原始索引的映射（保持同一分组内按 Excel 原始顺序）
        sheet_order = {name: idx for idx, name in enumerate(available_sheets)
                       if "HIS" in name.upper() and name != impl_summary_sheet_name}

        # 计算每个分组的最小优先级（用于分组间排序）
        group_priorities: dict[str, int] = {}
        for sheet_name in sheets_to_process:
            group_name, _ = self._parse_sheet_name_for_grouping(sheet_name)
            priority = self._priority_rules.get(sheet_name, 999)
            if group_name not in group_priorities:
                group_priorities[group_name] = priority
            else:
                group_priorities[group_name] = min(group_priorities[group_name], priority)

        def sort_key(sheet_name):
            group_name, sub_title = self._parse_sheet_name_for_grouping(sheet_name)
            group_priority = group_priorities.get(group_name, 999)
            sheet_priority = self._priority_rules.get(sheet_name, 999)
            original_order = sheet_order.get(sheet_name, 999)
            # 分组间按组最小优先级排序，分组内按 Sheet 优先级和原始顺序排序
            return (group_priority, group_name, sheet_priority, original_order)

        sheets_to_process.sort(key=sort_key)
        
        for sheet_name in sheets_to_process:
            section_data = self._parse_sheet(excel_file, sheet_name)

            # 过滤只有列头的空 Sheet（无实际任务数据）
            if section_data and section_data.get('task_count', 0) == 0:
                continue
            if section_data:
                sections.append(section_data)
                total_tasks += section_data.get('task_count', 0)
                
                # 收集风险告警
                for action_group in section_data.get('action_groups', []):
                    if action_group.get('is_high_risk'):
                        risk_alerts.append({
                            'sheet_name': sheet_name,
                            'action_type': action_group.get('action_type'),
                            'task_count': action_group.get('task_count', 0),
                            'task_names': [
                                t.get('cells', [''])[0] for t in action_group.get('tasks', [])
                            ]
                        })
                        high_risk_count += action_group.get('task_count', 0)
        
        # 构建最终输出
        result = {
            'meta': {
                'source_file': excel_file.name,
                'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                'version': self.PROTOCOL_VERSION
            },
            'summary': {
                'total_tasks': total_tasks,
                'total_sheets': len(sections),
                'high_risk_count': high_risk_count,
                'has_external_links': len(all_external_links) > 0,
                'external_links': all_external_links
            },
            'has_risk_alerts': len(risk_alerts) > 0,
            'risk_alerts': risk_alerts,
            'implementation_summary': implementation_summary,
            'sections': sections
        }
        
        return result
    
    def _parse_implementation_summary(
        self, excel_file: Path, available_sheets: list[str]
    ) -> dict:
        """
        解析实施总表（固定从「变更安排」Sheet 获取）

        处理合并单元格表头，提取固定5列：
        任务序号、变更内容、变更事项、实施人、复核人

        Returns:
            implementation_summary 字典，columns 固定为 5 列顺序

        Raises:
            ValueError: 当「变更安排」Sheet 不存在时抛出
        """
        # 固定从「变更安排」Sheet 获取实施总表
        target_sheet = "变更安排"
        if target_sheet not in available_sheets:
            raise ValueError(f"Excel 文件中缺少必需的 Sheet 页: {target_sheet}")

        # 目标列名及别名映射（固定5列）
        target_columns = {
            '任务序号': ['任务序号', '序号', 'No', 'NO'],
            '变更内容': ['变更内容', '内容'],
            '变更事项': ['变更事项', '事项'],
            '实施人': ['实施人', '执行人'],
            '复核人': ['复核人', '检查人']
        }

        try:
            wb = load_workbook(excel_file, read_only=True, data_only=True)
            ws = wb[target_sheet]

            # 1. 从合并单元格中提取表头（第1行或合并区域的值）
            header_row = 1  # 表头在第1行（合并单元格的值在左上角）

            # 获取所有列的表头值
            col_headers = {}
            for col_idx in range(1, ws.max_column + 1):
                cell = ws.cell(row=header_row, column=col_idx)
                value = str(cell.value).strip() if cell.value else ''
                if value:
                    col_headers[col_idx] = value

            # 2. 匹配目标列
            col_mapping = {}  # {标准列名: 列索引}
            for std_col, aliases in target_columns.items():
                for col_idx, header in col_headers.items():
                    # 精确匹配
                    if header in aliases:
                        col_mapping[std_col] = col_idx
                        break
                    # 部分匹配
                    for alias in aliases:
                        if alias in header:
                            col_mapping[std_col] = col_idx
                            break
                    else:
                        continue
                    break

            # 3. 读取数据行
            # 检测数据起始行：如果第2行全是空值或与第1行相同（合并单元格），则从第3行开始
            data_start_row = 2
            if ws.max_row >= 2:
                row2_has_data = False
                for col_idx in col_mapping.values():
                    cell = ws.cell(row=2, column=col_idx)
                    if cell.value and str(cell.value).strip():
                        row2_has_data = True
                        break
                if not row2_has_data:
                    data_start_row = 3

            rows = []
            for row_idx in range(data_start_row, ws.max_row + 1):
                cells = []
                has_data = False
                for std_col in ['任务序号', '变更内容', '变更事项', '实施人', '复核人']:
                    col_idx = col_mapping.get(std_col)
                    if col_idx:
                        cell = ws.cell(row=row_idx, column=col_idx)
                        value = str(cell.value).strip() if cell.value else ''
                        cells.append(self._sanitize_string(value))
                        if value:
                            has_data = True
                    else:
                        cells.append('')

                # 跳过空行
                if has_data:
                    rows.append({'cells': cells})

            wb.close()

            return {
                'sheet_name': target_sheet,
                'columns': ['任务序号', '变更内容', '变更事项', '实施人', '复核人'],
                'rows': rows,
                'has_data': len(rows) > 0
            }

        except Exception as e:
            print(f"警告: 解析实施总表 '{target_sheet}' 时出错: {e}")
            return {
                'sheet_name': target_sheet,
                'columns': ['任务序号', '变更内容', '变更事项', '实施人', '复核人'],
                'rows': [],
                'has_data': False
            }
    
    def _parse_sheet(self, excel_file: Path, sheet_name: str) -> Optional[dict]:
        """
        解析单个 Sheet
        
        Args:
            excel_file: Excel 文件路径对象
            sheet_name: Sheet 名称
            
        Returns:
            章节数据字典，或 None（如果 Sheet 为空）
        """
        try:
            # 读取 Sheet 数据
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=0)
            
            # 空数据处理
            if df.empty:
                return None
            
            # 清洗数据：处理空值和非法字符
            df = self._clean_dataframe(df)
            
            # 动态表头解析：建立列名到核心字段的映射
            field_mapping = self._build_field_mapping(df.columns.tolist())
            
            # 验证必填字段
            self._validate_required_fields(field_mapping)
            
            # 提取核心字段数据
            action_column = field_mapping.get('action_type')
            task_name_column = field_mapping.get('task_name')
            deploy_unit_column = field_mapping.get('deploy_unit')
            executor_column = field_mapping.get('executor')
            external_link_column = field_mapping.get('external_link')
            
            # 获取该章节的列定义（用于 cells 提取）
            columns, column_mapping = self._get_columns_and_mapping_for_sheet(sheet_name)
            
            # 构建 Excel 实际列名 -> 标准列名 的反向映射
            std_to_excel = self._build_std_to_excel_mapping(
                df.columns.tolist(), column_mapping, columns
            )
            
            # 按 action_type 分组聚合
            # 聚合算法：相同 Sheet 下相同操作类型的任务合并为一组
            action_groups = {}
            
            for idx, row in df.iterrows():
                # 获取操作类型
                action_type = self._safe_get_value(row, action_column)
                if not action_type:
                    continue  # 跳过无操作类型的行
                
                action_type = str(action_type).strip()
                
                # 初始化操作组
                if action_type not in action_groups:
                    action_groups[action_type] = []
                
                # 构建任务数据
                task_data = {
                    'task_name': self._safe_get_value(row, task_name_column, ''),
                    'deploy_unit': self._safe_get_value(row, deploy_unit_column, ''),
                    'executor': self._safe_get_value(row, executor_column, ''),
                    'external_link': self._safe_get_value(row, external_link_column, ''),
                    'raw_data': self._extract_raw_data(row)
                }
                
                action_groups[action_type].append(task_data)
            
            # 构建 action_groups 列表
            formatted_action_groups = []
            for action_type, tasks in action_groups.items():
                # 从 action_library 获取操作说明
                action_config = self._action_library.get(action_type, {})
                
                # 判断是否高危操作
                is_high_risk = self._is_high_risk(action_type)
                
                # 将任务数据转换为 cells 数组格式（使用列名映射）
                formatted_tasks = []
                for task in tasks:
                    # 按列顺序提取 cells 数组，支持列名映射
                    cells = self._extract_cells_by_columns_with_mapping(
                        task.get('raw_data', {}), 
                        columns,
                        std_to_excel
                    )
                    formatted_tasks.append({'cells': cells})
                
                formatted_action_groups.append({
                    'action_type': action_type,
                    'instruction': action_config.get(
                        'instruction', 
                        f"执行以下{action_type}操作："
                    ),
                    'is_high_risk': is_high_risk,
                    'task_count': len(formatted_tasks),
                    'tasks': formatted_tasks
                })
            
            # 获取章节优先级
            priority = self._priority_rules.get(sheet_name, 999)

            # 解析 Sheet 名称，提取分组信息
            group_name, sub_title = self._parse_sheet_name_for_grouping(sheet_name)

            return {
                'section_name': sheet_name,
                'group_name': group_name,      # 分组名称（括号外内容）
                'sub_title': sub_title,        # 子标题（括号内内容，无括号时为 None）
                'priority': priority,
                'has_action_groups': len(formatted_action_groups) > 0,
                'columns': columns,
                'task_count': sum(len(g['tasks']) for g in formatted_action_groups),
                'action_groups': formatted_action_groups
            }
            
        except Exception as e:
            # 防御性编程：记录错误但不中断整个解析过程
            print(f"警告: 解析 Sheet '{sheet_name}' 时出错: {e}")
            return None
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗 DataFrame：处理空值和非法字符
        
        Args:
            df: 原始 DataFrame
            
        Returns:
            清洗后的 DataFrame
        """
        # 清理列名中的空白字符
        df.columns = df.columns.map(lambda x: str(x).strip() if pd.notna(x) else '')
        
        # 移除完全空白的行
        df = df.dropna(how='all')
        
        # 移除所有列都为空字符串的行
        df = df.loc[~(df == '').all(axis=1)]
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        return df
    
    def _build_field_mapping(self, columns: list[str]) -> dict[str, Optional[str]]:
        """
        建立核心字段到实际列名的映射（动态表头解析）
        
        通过 core_fields 中定义的别名，在 Excel 列名中查找匹配项
        支持大小写不敏感和部分匹配
        
        Args:
            columns: Excel 列名列表
            
        Returns:
            字段映射字典 {field_key: actual_column_name}
        """
        mapping = {}
        
        for field_key, field_config in self._core_fields.items():
            aliases = field_config.get('aliases', [])
            actual_column = None
            
            # 精确匹配（忽略大小写和空白）
            for col in columns:
                col_normalized = str(col).strip().lower()
                for alias in aliases:
                    if col_normalized == alias.lower().strip():
                        actual_column = col
                        break
                if actual_column:
                    break
            
            # 如果精确匹配失败，尝试包含匹配
            if not actual_column:
                for col in columns:
                    col_normalized = str(col).strip().lower()
                    for alias in aliases:
                        if alias.lower().strip() in col_normalized:
                            actual_column = col
                            break
                    if actual_column:
                        break
            
            mapping[field_key] = actual_column
        
        return mapping
    
    def _validate_required_fields(self, field_mapping: dict[str, Optional[str]]) -> None:
        """
        验证必填字段是否存在
        
        Args:
            field_mapping: 字段映射字典
            
        Raises:
            RequiredFieldMissingError: 必填字段缺失时抛出
        """
        missing_fields = []
        
        for field_key, field_config in self._core_fields.items():
            if field_config.get('required', False):
                if not field_mapping.get(field_key):
                    missing_fields.append(field_key)
        
        if missing_fields:
            raise RequiredFieldMissingError(
                f"必填字段缺失: {', '.join(missing_fields)}"
            )
    
    def _safe_get_value(
        self, 
        row: pd.Series, 
        column_name: Optional[str], 
        default: str = ''
    ) -> str:
        """
        安全获取单元格值，处理空值和非法字符
        
        Args:
            row: 数据行
            column_name: 列名
            default: 默认值
            
        Returns:
            清洗后的字符串值
        """
        if not column_name:
            return default
        
        value = row.get(column_name, default)
        
        # 处理 NaN
        if pd.isna(value):
            return default
        
        # 转换为字符串并清理非法字符
        str_value = str(value).strip()
        str_value = self._sanitize_string(str_value)
        
        return str_value if str_value else default
    
    def _sanitize_string(self, text: str) -> str:
        """
        清理字符串中的非法字符（控制字符等）
        
        Args:
            text: 原始字符串
            
        Returns:
            清理后的字符串
        """
        # 移除控制字符
        cleaned = self.ILLEGAL_CHAR_PATTERN.sub('', text)
        
        # 将连续空白替换为单个空格
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _extract_raw_data(self, row: pd.Series) -> dict:
        """
        提取原始行数据的完整字典（保留所有列）
        
        Args:
            row: 数据行
            
        Returns:
            原始数据字典
        """
        raw_data = {}
        for col in row.index:
            value = row[col]
            if pd.isna(value):
                raw_data[col] = ''
            else:
                raw_data[col] = self._sanitize_string(str(value))
        return raw_data
    
    def _is_high_risk(self, action_type: str) -> bool:
        """
        判断操作是否为高危操作
        
        Args:
            action_type: 操作类型
            
        Returns:
            是否高危
        """
        # 检查是否在 action_library 中标记为高危
        action_config = self._action_library.get(action_type, {})
        if action_config.get('is_high_risk', False):
            return True
        
        # 检查是否包含高危关键字
        for keyword in self._high_risk_keywords:
            if keyword in action_type:
                return True
        
        return False
    
    def _extract_cells_by_columns(self, raw_data: dict, columns: list[str]) -> list[str]:
        """
        从原始数据中按配置的列顺序提取单元格值
        
        Args:
            raw_data: 原始行数据字典 {列名: 值}
            columns: 列名列表（定义顺序）
            
        Returns:
            按列顺序排列的单元格值列表
        """
        cells = []
        for col in columns:
            # 从 raw_data 中按列名获取值，默认为空字符串
            value = raw_data.get(col, '')
            cells.append(str(value) if value else '')
        return cells
    
    def _get_columns_for_sheet(self, sheet_name: str) -> list[str]:
        """
        获取指定 Sheet 应展示的列名
        
        Args:
            sheet_name: Sheet 名称
            
        Returns:
            列名列表
        """
        if sheet_name in self._sheet_column_mapping:
            return self._sheet_column_mapping[sheet_name].get('columns', [])
        return self._default_columns
    
    def _get_columns_and_mapping_for_sheet(self, sheet_name: str) -> tuple[list[str], dict]:
        """
        获取指定 Sheet 应展示的列名和列名映射
        
        Args:
            sheet_name: Sheet 名称
            
        Returns:
            (列名列表, 列名映射字典)
        """
        if sheet_name in self._sheet_column_mapping:
            config = self._sheet_column_mapping[sheet_name]
            columns = config.get('columns', [])
            column_mapping = config.get('column_mapping', {})
            return columns, column_mapping
        return self._default_columns, {}
    
    def _build_std_to_excel_mapping(
        self, 
        excel_columns: list[str], 
        column_mapping: dict, 
        std_columns: list[str]
    ) -> dict[str, Optional[str]]:
        """
        构建标准列名 -> Excel 实际列名 的映射
        
        Args:
            excel_columns: Excel 实际列名列表
            column_mapping: 配置中的列名映射 {标准列: [别名列表]}
            std_columns: 标准列名列表（定义顺序）
            
        Returns:
            映射字典 {标准列名: Excel实际列名}
        """
        std_to_excel: dict[str, Optional[str]] = {}
        
        for std_col in std_columns:
            # 获取该标准列的别名列表
            aliases = column_mapping.get(std_col, [std_col])
            if isinstance(aliases, str):
                aliases = [aliases]
            
            # 在 Excel 列中查找匹配
            found = None
            for excel_col in excel_columns:
                excel_col_norm = str(excel_col).strip()
                for alias in aliases:
                    if str(alias).strip() == excel_col_norm:
                        found = excel_col
                        break
                if found:
                    break
            
            std_to_excel[std_col] = found
        
        return std_to_excel
    
    def _extract_cells_by_columns_with_mapping(
        self, 
        raw_data: dict, 
        columns: list[str],
        std_to_excel: dict[str, Optional[str]]
    ) -> list[str]:
        """
        从原始数据中按列顺序提取单元格值（支持列名映射）
        
        Args:
            raw_data: 原始行数据字典 {列名: 值}
            columns: 标准列名列表（定义顺序）
            std_to_excel: 标准列名 -> Excel 实际列名 映射
            
        Returns:
            按列顺序排列的单元格值列表
        """
        cells = []
        for std_col in columns:
            # 先通过映射找 Excel 实际列名
            excel_col = std_to_excel.get(std_col)
            if excel_col and excel_col in raw_data:
                value = raw_data.get(excel_col, '')
            else:
                # 映射失败，尝试直接用标准列名查找（兼容旧行为）
                value = raw_data.get(std_col, '')
            cells.append(str(value) if value else '')
        return cells
    
    def get_columns_for_sheet(self, sheet_name: str) -> list[str]:
        """
        获取指定 Sheet 应展示的列名（公开接口）
        
        Args:
            sheet_name: Sheet 名称
            
        Returns:
            列名列表
        """
        return self._get_columns_for_sheet(sheet_name)


# 便捷函数
def parse_excel(excel_path: str, config_path: str = "config/rules.yaml") -> dict:
    """
    解析 Excel 文件的便捷函数
    
    Args:
        excel_path: Excel 文件路径
        config_path: 规则配置文件路径
        
    Returns:
        符合 report_schema.md 规范的字典数据
    """
    parser = ExcelParser(config_path)
    return parser.parse(excel_path)
