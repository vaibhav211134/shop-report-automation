from __future__ import annotations

import json
import logging

import requests

from formatters import build_whatsapp_components


def send_whatsapp_templates(
    token: str,
    phone_id: str,
    template_name: str,
    report_date: str,
    parameters: list[dict[str, str]],
    destination_numbers: list[str],
    logger: logging.Logger,
) -> dict[str, bool]:
    """Send WhatsApp template message to all configured numbers."""
    if not token or not phone_id:
        logger.warning("WhatsApp credentials missing. Skipping WhatsApp sends.")
        return {number: False for number in destination_numbers}

    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    components = build_whatsapp_components(report_date, parameters)

    status_map: dict[str, bool] = {}
    for number in destination_numbers:
        payload = {
            "messaging_product": "whatsapp",
            "to": number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "en"},
                "components": components,
            },
        }

        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        status = response.status_code == 200
        status_map[number] = status
        if status:
            logger.info("WhatsApp sent to %s", number)
        else:
            logger.error(
                "WhatsApp send failed for %s. status=%s body=%s",
                number,
                response.status_code,
                response.text,
            )
    return status_map
