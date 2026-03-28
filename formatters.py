from __future__ import annotations

from typing import Any

from config.settings import RunContext
from data_processor import ReportTotals


def format_currency(amount: float) -> str:
    """Return amount in INR-style comma formatting."""
    return f"{amount:,.0f}"

def build_telegram_message(
    context: RunContext, 
    totals: ReportTotals, 
    shop_order: list[str]
) -> str:
    """Build Telegram markdown message body."""
    
    message = f"📦 *Sitaram Sales Report* 📦\n\n📊 *{context.report_title}*\n\n"

    for shop in shop_order:
        sales = totals.shop_net_sales.get(shop, 0.0)
        message += f"🏪 *{shop}*\n"
        message += f"💰 Net Sales: ₹{format_currency(sales)}\n"
 
        if context.is_morning:
            expense = totals.shop_expenses.get(shop, 0.0)
            message += f"📤 Expense: ₹{format_currency(expense)}\n\n"
     
        else:
            message += "\n"

    message += f"{'=' * 20}\n"
    message += f"📊 *Total Net Sales: ₹{format_currency(totals.total_sales)}*\n"

    if context.is_morning:
        message += f"💸 *Total Expense: ₹{format_currency(totals.total_expenses)}*\n"
    else:
        message += "\n_💡 Full report tomorrow morning._\n"
   
    return message

def build_whatsapp_parameters(
    context: RunContext,
    totals: ReportTotals,
    shop_order: list[str],
) -> list[dict[str, str]]:
    """Build WhatsApp template text parameters in expected order."""
    parameters: list[dict[str, str]] = []
    if context.is_morning:
        for shop in shop_order:
            parameters.append({"type": "text", "text": format_currency(totals.shop_net_sales.get(shop, 0.0))})
            parameters.append({"type": "text", "text": format_currency(totals.shop_expenses.get(shop, 0.0))})
        parameters.append({"type": "text", "text": format_currency(totals.total_sales)})
        parameters.append({"type": "text", "text": format_currency(totals.total_expenses)})
        return parameters

    for shop in shop_order:
        parameters.append({"type": "text", "text": format_currency(totals.shop_net_sales.get(shop, 0.0))})
    parameters.append({"type": "text", "text": format_currency(totals.total_sales)})
    return parameters


def build_whatsapp_components(report_date: str, parameters: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Build WhatsApp header/body components for template payload."""
    return [
        {
            "type": "header",
            "parameters": [{"type": "text", "text": report_date}],
        },
        {
            "type": "body",
            "parameters": parameters,
        },
    ]
