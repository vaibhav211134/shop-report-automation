"""Tests for message formatting helpers."""

from __future__ import annotations

from config.settings import RunContext
from data_processor import ReportTotals
from formatters import build_telegram_message, build_whatsapp_parameters, format_currency


def test_format_currency() -> None:
    """Currency helper uses comma grouping with integer rounding."""
    assert format_currency(1234567.49) == "1,234,567"


def test_whatsapp_parameters_morning() -> None:
    """Morning template contains per-shop sales and expense pairs plus totals."""
    context = RunContext(
        is_morning=True,
        report_date="26 Mar 2026",
        report_title="Complete Report of 26 Mar 2026",
        target_keyword="yesterday",
        whatsapp_template_name="sitaram_daily_full_report",
    )
    totals = ReportTotals(
        shop_net_sales={"SITARAM AND SONS": 1000.0},
        shop_expenses={"SITARAM AND SONS": 200.0},
        total_sales=1000.0,
        total_expenses=200.0,
    )
    params = build_whatsapp_parameters(context, totals, ["SITARAM AND SONS"])
    assert params == [
        {"type": "text", "text": "1,000"},
        {"type": "text", "text": "200"},
        {"type": "text", "text": "1,000"},
        {"type": "text", "text": "200"},
    ]


def test_telegram_message_evening_has_hint() -> None:
    """Evening message includes tomorrow full-report hint."""
    context = RunContext(
        is_morning=False,
        report_date="27 Mar 2026",
        report_title="Sales so far for 27 Mar 2026",
        target_keyword="today",
        whatsapp_template_name="sitaram_evening_sales_flash",
    )
    totals = ReportTotals(
        shop_net_sales={"SITARAM AND SONS": 1000.0},
        shop_expenses={},
        total_sales=1000.0,
        total_expenses=0.0,
    )
    message = build_telegram_message(context, totals, ["SITARAM AND SONS"])
    assert "Full report tomorrow morning" in message
