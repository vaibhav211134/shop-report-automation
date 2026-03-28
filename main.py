from __future__ import annotations

import sys
import json
from datetime import datetime
from pathlib import Path

from config.logger import setup_logger
from config.settings import Config, build_run_context
from data_processor import compute_report_totals, load_report_dataframe
from formatters import build_telegram_message, build_whatsapp_parameters
from gmail_downloader import download_latest_report
from telegram_sender import send_telegram_message
from whatsapp_sender import send_whatsapp_templates


def run() -> int:
    """Execute report generation and messaging pipeline."""
    logger = setup_logger(str(Config.LOG_DIR / "app.log"))
    logger.info("Pipeline started.")

    try:
        # 1. Resolve Runtime Context (Morning vs Evening)
        context = build_run_context()
        logger.info(
            "Run context resolved. period=%s template=%s",
            "morning" if context.is_morning else "evening",
            context.whatsapp_template_name,
        )

        # 2. Download and Process Data
        report_file = download_latest_report(context.target_keyword, logger)
        logger.info("Report file ready: %s", report_file)

        dataframe = load_report_dataframe(report_file)
        totals = compute_report_totals(dataframe)
        logger.info(
            "Data processing complete. total_sales=%s total_expenses=%s",
            totals.total_sales,
            totals.total_expenses,
        )

        # 3. Prepare Messaging Parameters
        shop_order = Config.shop_order()
        family_numbers = Config.family_numbers()
        telegram_message = build_telegram_message(context, totals, shop_order)
        whatsapp_parameters = build_whatsapp_parameters(context, totals, shop_order)
        logger.info("Formatting complete. whatsapp_vars=%d", len(whatsapp_parameters))

        # 4. Send Notifications (Telegram & WhatsApp)
        send_telegram_message(
            bot_token=Config.TELEGRAM_BOT_TOKEN,
            chat_id=Config.TELEGRAM_CHAT_ID,
            message=telegram_message,
            logger=logger,
        )
        send_whatsapp_templates(
            token=Config.WHATSAPP_TOKEN,
            phone_id=Config.WHATSAPP_PHONE_ID,
            template_name=context.whatsapp_template_name,
            report_date=context.report_date,
            parameters=whatsapp_parameters,
            destination_numbers=family_numbers,
            logger=logger,
        )

        # 5. DATA PERSISTENCE (The Dashboard Engine)
        # ---------------------------------------------------------
        Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        # Prepare the data entry
        current_data = {
            "report_date": context.report_date,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_sales": totals.total_sales,
            "total_expenses": totals.total_expenses,
            "is_morning": context.is_morning,
            "shops": [
                {
                    "name": shop,
                    "sales": totals.shop_net_sales.get(shop, 0.0),
                    "expenses": totals.shop_expenses.get(shop, 0.0) if context.is_morning else 0.0
                }
                for shop in shop_order
            ]
        }

        # A. Save Snapshot (latest_summary.json)
        summary_path = Config.DATA_DIR / "latest_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=4)
        logger.info("Live snapshot saved to %s", summary_path)

        # B. Update Ledger (history.json)
        history_path = Config.DATA_DIR / "history.json"
        history_data = []

        if history_path.exists():
            try:
                with open(history_path, "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    # SAFETY CHECK: Ensure the loaded data is actually a list
                    if isinstance(loaded_data, list):
                        history_data = loaded_data
                    else:
                        logger.warning("history.json was not a list. Resetting to empty.")
            except json.JSONDecodeError:
                logger.warning("History file corrupted, starting fresh.")

        # Check if we already have an entry for this exact date to avoid duplicates
        # SAFETY CHECK: Ensure 'entry' is a dict before looking for 'report_date'
        existing_entry_idx = next(
            (i for i, entry in enumerate(history_data) 
             if isinstance(entry, dict) and entry.get("report_date") == context.report_date), 
            None
        )

        if existing_entry_idx is not None:
            history_data[existing_entry_idx] = current_data
            logger.info("Updated existing history entry for %s", context.report_date)
        else:
            history_data.append(current_data)
            logger.info("Appended new history entry for %s", context.report_date)

        # Keep only the last 30 reports to keep things snappy
        history_data = history_data[-30:]

        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=4)
        
        # ---------------------------------------------------------

        logger.info("Pipeline completed successfully.")
        return 0

    except Exception:
        logger.exception("Pipeline failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run())