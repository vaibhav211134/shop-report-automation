from __future__ import annotations

import logging

import requests


def send_telegram_message(
    bot_token: str,
    chat_id: str,
    message: str,
    logger: logging.Logger,
) -> bool:
    """Send markdown report message to Telegram."""
    if not bot_token or not chat_id:
        logger.warning("Telegram credentials missing. Skipping Telegram send.")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, data=payload, timeout=30)
    if response.status_code == 200:
        logger.info("Telegram sent successfully.")
        return True

    logger.error("Telegram send failed. status=%s body=%s", response.status_code, response.text)
    return False
