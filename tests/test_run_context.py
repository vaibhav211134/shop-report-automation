"""Tests for runtime context selection logic."""

from __future__ import annotations

from datetime import datetime, timezone

from config.settings import build_run_context


def test_build_run_context_morning() -> None:
    """Before 3 PM IST, context should be morning mode."""
    dt = datetime(2026, 3, 27, 8, 0, tzinfo=timezone.utc)
    context = build_run_context(dt)
    assert context.is_morning is True
    assert context.target_keyword == "yesterday"
    assert context.whatsapp_template_name == "sitaram_daily_full_report"


def test_build_run_context_evening() -> None:
    """After 3 PM IST, context should be evening mode."""
    dt = datetime(2026, 3, 27, 12, 0, tzinfo=timezone.utc)
    context = build_run_context(dt)
    assert context.is_morning is False
    assert context.target_keyword == "today"
    assert context.whatsapp_template_name == "sitaram_evening_sales_flash"
