from __future__ import annotations

import sys

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
        context = build_run_context()
        logger.info(
            "Run context resolved. period=%s template=%s",
            "morning" if context.is_morning else "evening",
            context.whatsapp_template_name,
        )

        report_file = download_latest_report(context.target_keyword, logger)
        logger.info("Report file ready: %s", report_file)

        dataframe = load_report_dataframe(report_file)
        totals = compute_report_totals(dataframe)
        logger.info(
            "Data processing complete. total_sales=%s total_expenses=%s",
            totals.total_sales,
            totals.total_expenses,
        )

        shop_order = Config.shop_order()
        family_numbers = Config.family_numbers()
        telegram_message = build_telegram_message(context, totals, shop_order)
        whatsapp_parameters = build_whatsapp_parameters(context, totals, shop_order)
        logger.info("Formatting complete. whatsapp_vars=%d", len(whatsapp_parameters))

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
        logger.info("Pipeline completed successfully.")
        return 0
    except Exception:
        logger.exception("Pipeline failed.")
        return 1


if __name__ == "__main__":
    sys.exit(run())
