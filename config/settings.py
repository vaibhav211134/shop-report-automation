from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

@dataclass(frozen=True)
class RunContext:
    """Runtime context derived from current IST time."""
    is_morning: bool
    report_date: str
    report_title: str
    target_keyword: str
    whatsapp_template_name: str

def build_run_context(now: datetime | None = None) -> RunContext:
    """Build run context for morning/evening reporting behavior."""
    ist_timezone = timezone(timedelta(hours=5, minutes=30))
    now_ist = now.astimezone(ist_timezone) if now else datetime.now(ist_timezone)

    if now_ist.hour < 15:
        report_date = (now_ist - timedelta(days=1)).strftime("%d %b %Y")
        return RunContext(
            is_morning=True,
            report_date=report_date,
            report_title=f"Complete Report of {report_date}",
            target_keyword="yesterday",
            whatsapp_template_name="sitaram_daily_full_report",
        )

    report_date = now_ist.strftime("%d %b %Y")
    return RunContext(
        is_morning=False,
        report_date=report_date,
        report_title=f"Sales so far for {report_date}",
        target_keyword="today",
        whatsapp_template_name="sitaram_evening_sales_flash",
    )

class Config:
    """Central configuration container for the app."""

    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOG_DIR: Path = BASE_DIR / "logs"
    TOKEN_FILE: Path = BASE_DIR / "token.json"
    GMAIL_SCOPES: list[str] = ["https://www.googleapis.com/auth/gmail.readonly"]
    DOWNLOADED_REPORT_BASENAME: str = "today_report"

    # API Keys & Secrets (Loaded from .env)
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")

    # PRIVATE DATA: We pull these from .env now to keep them off GitHub
    # Format in .env should be: FAMILY_NUMBERS=91XXXXXXXXXX,91YYYYYYYYYY
    _RAW_NUMBERS = os.getenv("FAMILY_NUMBERS", "910000000000")
    _RAW_SHOPS = os.getenv("SHOP_ORDER", "Shop 1,Shop 2,Shop 3,Shop 4")

    DEFAULT_FAMILY_NUMBERS: list[str] = [n.strip() for n in _RAW_NUMBERS.split(",")]
    DEFAULT_SHOP_ORDER: list[str] = [s.strip() for s in _RAW_SHOPS.split(",")]

    @classmethod
    def load_client_config(cls, file_name: str = "client_config.yaml") -> dict[str, Any]:
        """Load optional client-specific config from YAML (Added to .gitignore)."""
        config_path = cls.BASE_DIR / file_name
        if not config_path.exists():
            return {}
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        return data

    @classmethod
    def family_numbers(cls) -> list[str]:
        """Return destination WhatsApp numbers from client config or environment."""
        client_cfg = cls.load_client_config()
        numbers = client_cfg.get("family_numbers", cls.DEFAULT_FAMILY_NUMBERS)
        return [str(number) for number in numbers]

    @classmethod
    def shop_order(cls) -> list[str]:
        """Return fixed shop order from client config or environment."""
        client_cfg = cls.load_client_config()
        shops = client_cfg.get("shop_order", cls.DEFAULT_SHOP_ORDER)
        return [str(shop) for shop in shops]