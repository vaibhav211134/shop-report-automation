from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config.settings import Config


def _is_supported_report(filename: str) -> bool:
    """Return True when attachment extension is supported."""
    lowered = filename.lower()
    return lowered.endswith(".csv") or lowered.endswith(".xlsx") or lowered.endswith(".xls")


def _download_attachment(
    service: Any,
    message_id: str,
    attachment_id: str,
    filename: str,
    logger: logging.Logger,
) -> Path:
    """Download a Gmail attachment and persist it under data directory."""
    attachment = (
        service.users()
        .messages()
        .attachments()
        .get(userId="me", messageId=message_id, id=attachment_id)
        .execute()
    )
    file_data = base64.urlsafe_b64decode(attachment["data"].encode("UTF-8"))

    extension = filename.split(".")[-1]
    output_path = Config.DATA_DIR / f"{Config.DOWNLOADED_REPORT_BASENAME}.{extension}"
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(file_data)
    logger.info("Downloaded attachment %s to %s", filename, output_path)
    return output_path


def download_latest_report(target_keyword: str, logger: logging.Logger) -> Path:
    """Download latest matching report file from Gmail attachments."""
    logger.info("Connecting to Gmail API.")
    creds = Credentials.from_authorized_user_file(
        str(Config.TOKEN_FILE),
        Config.GMAIL_SCOPES,
    )
    service = build("gmail", "v1", credentials=creds)

    results = service.users().messages().list(userId="me", q="has:attachment", maxResults=1).execute()
    messages = results.get("messages", [])
    if not messages:
        raise RuntimeError("No emails with attachments found.")

    message_id = messages[0]["id"]
    message = service.users().messages().get(userId="me", id=message_id).execute()
    parts = message.get("payload", {}).get("parts", [])

    for part in parts:
        filename = part.get("filename", "")
        if filename and _is_supported_report(filename) and target_keyword.lower() in filename.lower():
            attachment_id = part.get("body", {}).get("attachmentId")
            if attachment_id:
                return _download_attachment(service, message_id, attachment_id, filename, logger)

    logger.warning("No keyword match for '%s'. Falling back to first valid attachment.", target_keyword)
    for part in parts:
        filename = part.get("filename", "")
        if filename and _is_supported_report(filename):
            attachment_id = part.get("body", {}).get("attachmentId")
            if attachment_id:
                return _download_attachment(service, message_id, attachment_id, filename, logger)

    raise RuntimeError("No CSV/Excel attachment found in latest email.")
