"""Tests for pandas data processing logic."""

from __future__ import annotations

import pandas as pd

from data_processor import ReportTotals, compute_report_totals


def test_compute_report_totals(sample_dataframe: pd.DataFrame) -> None:
    """It calculates per-shop and overall totals correctly."""
    totals: ReportTotals = compute_report_totals(sample_dataframe)

    assert totals.shop_net_sales["SITARAM AND SONS"] == 900.0
    assert totals.shop_net_sales["SITARAM SHANKAR LAL"] == 500.0
    assert totals.shop_expenses["SITARAM AND SONS"] == 200.0
    assert totals.shop_expenses["SITARAM SHANKAR LAL"] == 50.0
    assert totals.total_sales == 1400.0
    assert totals.total_expenses == 250.0
