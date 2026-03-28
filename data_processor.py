from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ReportTotals:
    """Aggregated report metrics by shop and totals."""

    shop_net_sales: dict[str, float]
    shop_expenses: dict[str, float]
    total_sales: float
    total_expenses: float


def load_report_dataframe(file_path: Path) -> pd.DataFrame:
    """Load report file from CSV/XLS/XLSX into a DataFrame."""
    path_as_string = str(file_path).lower()
    if path_as_string.endswith(".csv"):
        dataframe = pd.read_csv(file_path, encoding="utf-8")
    elif path_as_string.endswith(".xlsx") or path_as_string.endswith(".xls"):
        dataframe = pd.read_excel(file_path, skiprows=5)
    else:
        raise ValueError(f"Unsupported file type for {file_path}")

    dataframe.columns = dataframe.columns.str.strip()
    return dataframe


def compute_report_totals(dataframe: pd.DataFrame) -> ReportTotals:
    """Compute net sales and expenses grouped by company."""
    working_df = dataframe.copy()
    working_df["Debit Amount"] = working_df["Debit Amount"].fillna(0)
    working_df["Credit Amount"] = working_df["Credit Amount"].fillna(0)

    sales_data = working_df[working_df["Voucher Type"] == "Sales"]
    returns_data = working_df[working_df["Voucher Type"] == "Sales Return"]
    expense_data = working_df[working_df["Voucher Type"] == "Payment"]

    shop_gross_sales = sales_data.groupby("Company Name")["Debit Amount"].sum()
    shop_returns = returns_data.groupby("Company Name")["Credit Amount"].sum()
    shop_expenses = expense_data.groupby("Company Name")["Debit Amount"].sum()
    shop_net_sales = shop_gross_sales.sub(shop_returns, fill_value=0)

    return ReportTotals(
        shop_net_sales={str(key): float(value) for key, value in shop_net_sales.to_dict().items()},
        shop_expenses={str(key): float(value) for key, value in shop_expenses.to_dict().items()},
        total_sales=float(shop_net_sales.sum()),
        total_expenses=float(shop_expenses.sum()),
    )
