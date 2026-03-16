# -*- coding: utf-8 -*-
"""
Excel Reader Module
负责 Excel 数据读取和基础清洗

单一职责：
- 读取 Excel 文件
- 获取 Sheet 列表
- 清洗 DataFrame（处理空值、列名清理）
"""

import warnings
from pathlib import Path
from typing import List, Optional

import pandas as pd
from openpyxl import load_workbook

# 抑制 openpyxl 的 DataValidation 警告
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


class ExcelReader:
    """
    Excel 数据读取器

    职责：
    - 读取 Excel 文件
    - 获取 Sheet 名称列表
    - 清洗 DataFrame（处理空值、列名清理）
    """

    def __init__(self, excel_path: str):
        """
        初始化 Excel 读取器

        Args:
            excel_path: Excel 文件路径
        """
        self.excel_path = Path(excel_path)
        self._workbook: Optional[object] = None

    def validate_file(self) -> None:
        """
        验证文件是否存在

        Raises:
            FileNotFoundError: 文件不存在时抛出
        """
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel 文件不存在: {self.excel_path}")

    def get_sheet_names(self) -> List[str]:
        """
        获取所有 Sheet 名称

        Returns:
            Sheet 名称列表
        """
        self.validate_file()

        workbook = load_workbook(self.excel_path, read_only=True, data_only=True)
        names = workbook.sheetnames
        workbook.close()
        return names

    def read_sheet(self, sheet_name: str, header: int = 0) -> pd.DataFrame:
        """
        读取指定 Sheet

        Args:
            sheet_name: Sheet 名称
            header: 表头行索引，默认 0

        Returns:
            清洗后的 DataFrame
        """
        self.validate_file()

        df = pd.read_excel(self.excel_path, sheet_name=sheet_name, header=header)
        return self.clean_dataframe(df)

    def read_sheet_raw(self, sheet_name: str, header: int = 0) -> pd.DataFrame:
        """
        读取指定 Sheet（不清洗）

        Args:
            sheet_name: Sheet 名称
            header: 表头行索引，默认 0

        Returns:
            原始 DataFrame
        """
        self.validate_file()

        return pd.read_excel(self.excel_path, sheet_name=sheet_name, header=header)

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗 DataFrame：处理空值和非法字符

        Args:
            df: 原始 DataFrame

        Returns:
            清洗后的 DataFrame
        """
        if df.empty:
            return df

        # 清理列名中的空白字符
        df.columns = df.columns.map(lambda x: str(x).strip() if pd.notna(x) else '')

        # 移除完全空白的行
        df = df.dropna(how='all')

        # 移除所有列都为空字符串的行
        df = df.loc[~(df == '').all(axis=1)]

        # 重置索引
        df = df.reset_index(drop=True)

        return df

    @property
    def file_name(self) -> str:
        """获取文件名"""
        return self.excel_path.name

    def __repr__(self) -> str:
        return f"ExcelReader({self.excel_path})"
