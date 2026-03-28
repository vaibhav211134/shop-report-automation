from __future__ import annotations

import sys

from main import run


if __name__ == "__main__":
    sys.exit(run())
import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
import requests
import urllib.parse
import json
from datetime import datetime, timedelta, timezone
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# ==========================================
# PART 1: CREDENTIALS
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")

FAMILY_NUMBERS = [
    '917766905770'
]

# ==========================================
# CRITICAL: SHOP ORDER MUST MATCH TEMPLATE
# Variables {{1}} to {{10}} are position-based
# If order is wrong, wrong data goes to wrong shop
# ==========================================
SHOP_ORDER = [
    "SITARAM AND SONS",
    "SITARAM SHANKAR LAL",
    "SITARAM SHYAM SUNDER",
    "SITARAMS"
]

# ==========================================
# PART 2: DETERMINE MORNING VS EVENING RUN
# ==========================================
ist_timezone = timezone(timedelta(hours=5, minutes=30))
now_ist = datetime.now(ist_timezone)

if now_ist.hour < 15:
    # Morning run → Full report of YESTERDAY
    is_morning = True
    report_date = (now_ist - timedelta(days=1)).strftime("%d %b %Y")
    report_title = f"Complete Report of {report_date}"
    target_keyword = "yesterday"
    whatsapp_template_name = "sitaram_daily_full_report"
else:
    # Evening run → Sales only of TODAY
    is_morning = False
    report_date = now_ist.strftime("%d %b %Y")
    report_title = f"Sales so far for {report_date}"
    target_keyword = "today"
    whatsapp_template_name = "sitaram_evening_sales_flash"

print(f"{'🌅 Morning' if is_morning else '🌆 Evening'} run detected → Using template: {whatsapp_template_name}")

# ==========================================
# PART 3: DOWNLOAD CSV OR EXCEL VIA GMAIL API
# ==========================================
print("Connecting to Gmail API...")

creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/gmail.readonly'])
service = build('gmail', 'v1', credentials=creds)

results = service.users().messages().list(userId='me', q="has:attachment", maxResults=1).execute()
messages = results.get('messages', [])

if not messages:
    print("❌ No emails with attachments found.")
    exit()

msg_id = messages[0]['id']
message = service.users().messages().get(userId='me', id=msg_id).execute()

file_downloaded = False
saved_file_path = "" # We will store the dynamic file name here

for part in message['payload'].get('parts', []):
    filename = part.get('filename', '')
    
    # Check if the file is a CSV or an Excel file
    if filename and (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
        if target_keyword in filename.lower():
            attachment_id = part['body'].get('attachmentId')
            attachment = service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=attachment_id
            ).execute()
            file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
            
            # Extract the actual extension and save dynamically
            file_extension = filename.split('.')[-1]
            saved_file_path = f"today_report.{file_extension}"
            
            with open(saved_file_path, "wb") as f:
                f.write(file_data)
            print(f"✅ Downloaded: {filename} as {saved_file_path}")
            file_downloaded = True
            break

if not file_downloaded:
    print(f"⚠️ '{target_keyword}' file not found. Falling back to first valid attachment.")
    for part in message['payload'].get('parts', []):
        filename = part.get('filename', '')
        if filename and (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
            attachment_id = part['body'].get('attachmentId')
            attachment = service.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=attachment_id
            ).execute()
            file_data = base64.urlsafe_b64decode(attachment['data'].encode('UTF-8'))
            
            file_extension = filename.split('.')[-1]
            saved_file_path = f"today_report.{file_extension}"
            
            with open(saved_file_path, "wb") as f:
                f.write(file_data)
            print(f"✅ Fallback downloaded: {filename} as {saved_file_path}")
            break

# Kill the script cleanly if no valid file was found
if not saved_file_path:
    print("❌ Could not find any CSV or Excel attachments in the latest email.")
    exit()

# ==========================================
# PART 4: PANDAS DATA ANALYSIS
# ==========================================
print(f"Processing data from {saved_file_path}...")

# Dynamically choose how to read the file based on its extension
if saved_file_path.endswith('.csv'):
    df = pd.read_csv(saved_file_path, encoding='utf-8')
elif saved_file_path.endswith('.xlsx') or saved_file_path.endswith('.xls'):
    df = pd.read_excel(saved_file_path, skiprows=5)

df.columns = df.columns.str.strip()

df['Debit Amount'] = df['Debit Amount'].fillna(0)
df['Credit Amount'] = df['Credit Amount'].fillna(0)

sales_data = df[df['Voucher Type'] == 'Sales']
returns_data = df[df['Voucher Type'] == 'Sales Return']
expense_data = df[df['Voucher Type'] == 'Payment']

shop_gross_sales = sales_data.groupby('Company Name')['Debit Amount'].sum()
shop_returns = returns_data.groupby('Company Name')['Credit Amount'].sum()
shop_expenses = expense_data.groupby('Company Name')['Debit Amount'].sum()

shop_net_sales = shop_gross_sales.sub(shop_returns, fill_value=0)

total_sales = shop_net_sales.sum()
total_expenses = shop_expenses.sum()

# ==========================================
# PART 5: FORMAT TELEGRAM MESSAGE
# ==========================================
telegram_message = f"📦 *Sitaram Sales Report* 📦\n\n📊 *{report_title}*\n\n"

for shop in SHOP_ORDER:
    sales = shop_net_sales.get(shop, 0)
    telegram_message += f"🏪 *{shop}*\n"
    telegram_message += f"💰 Net Sales: ₹{sales:,.0f}\n"
    if is_morning:
        expense = shop_expenses.get(shop, 0)
        telegram_message += f"📤 Expense: ₹{expense:,.0f}\n\n"
    else:
        telegram_message += "\n"

telegram_message += f"{'='*20}\n"
telegram_message += f"📊 *Total Net Sales: ₹{total_sales:,.0f}*\n"
if is_morning:
    telegram_message += f"💸 *Total Expense: ₹{total_expenses:,.0f}*\n"
else:
    telegram_message += f"\n_💡 Full report tomorrow morning._\n"

# ==========================================
# PART 6: BUILD WHATSAPP TEMPLATE PARAMETERS
# ==========================================
def format_amount(value):
    """Format number for WhatsApp — no ₹ symbol (already in template)"""
    return f"{value:,.0f}"

if is_morning:
    # Morning: 10 variables
    # {{1}}{{2}} = shop1 sales/exp ... {{9}}{{10}} = totals
    parameters = []
    for shop in SHOP_ORDER:
        sales = shop_net_sales.get(shop, 0)
        expense = shop_expenses.get(shop, 0)
        parameters.append({"type": "text", "text": format_amount(sales)})
        parameters.append({"type": "text", "text": format_amount(expense)})
    parameters.append({"type": "text", "text": format_amount(total_sales)})
    parameters.append({"type": "text", "text": format_amount(total_expenses)})

else:
    # Evening: 5 variables
    # {{1}}{{2}}{{3}}{{4}} = shop sales, {{5}} = total sales
    parameters = []
    for shop in SHOP_ORDER:
        sales = shop_net_sales.get(shop, 0)
        parameters.append({"type": "text", "text": format_amount(sales)})
    parameters.append({"type": "text", "text": format_amount(total_sales)})

print(f"📋 Template: {whatsapp_template_name} | Variables: {len(parameters)}")

# ==========================================
# PART 7: SEND TO TELEGRAM
# ==========================================
print("Sending to Telegram...")
encoded_message = urllib.parse.quote(telegram_message)
url_tg = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={encoded_message}&parse_mode=Markdown"

try:
    response_tg = requests.get(url_tg)
    if response_tg.status_code == 200:
        print("✅ Telegram sent successfully.")
    else:
        print(f"❌ Telegram Error: {response_tg.text}")
except Exception as e:
    print(f"⚠️ Telegram failed: {e}")

# ==========================================
# PART 8: SEND TO WHATSAPP
# ==========================================
print("Sending to WhatsApp...")
url_wa = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_ID}/messages"

headers_wa = {
    "Authorization": f"Bearer {WHATSAPP_TOKEN}",
    "Content-Type": "application/json"
}

for number in FAMILY_NUMBERS:
    print(f"🔄 Processing number: {number}...") 

    # --- Build components based on morning or evening ---
    if is_morning:
        components = [
            {
                "type": "header",
                "parameters": [
                    {"type": "text", "text": report_date}   # fills {{1}} in header
                ]
            },
            {
                "type": "body",
                "parameters": parameters   # 10 variables
            }
        ]
    else:
        components = [
            {
                "type": "header",
                "parameters": [
                    {"type": "text", "text": report_date}   # fills {{1}} in header
                ]
            },
            {
                "type": "body",
                "parameters": parameters   # 5 variables
            }
        ]

    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "template",
        "template": {
            "name": whatsapp_template_name,
            "language": {"code": "en"},
            "components": components
        }
    }

    try:
        response_wa = requests.post(url_wa, headers=headers_wa, data=json.dumps(payload))
        if response_wa.status_code == 200:
            print(f"✅ WhatsApp sent to {number}")
        else:
            print(f"❌ WhatsApp Error for {number}: {response_wa.text}")
    except Exception as e:
        print(f"⚠️ WhatsApp failed for {number}: {e}")