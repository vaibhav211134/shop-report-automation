<div align="center">

# 📦 Retail Report Automation

**A production-grade pipeline that automatically analyses Tally ERP exports and delivers daily sales reports to WhatsApp and Telegram — zero manual effort.**

Built for a 40-year-old family clothing business in Bihar running 4 shops.
Now saves 30 minutes every day and has eliminated manual reporting entirely.

## The Problem

Every evening, someone in the family had to manually pull numbers from Tally, calculate net sales across 4 shops, and type it into a WhatsApp group. This took 30 minutes, happened at the end of a long day, and was prone to errors.

This system replaced that entirely.

---

## What It Does

The pipeline runs **twice every day on its own** via GitHub Actions — no server, no manual trigger.

```
9:00 AM  →  Full report of yesterday   (net sales + expenses per shop + totals)
6:00 PM  →  Sales flash for today      (net sales per shop + running total)
```

Each run:
1. Connects to Gmail and downloads the latest Tally export (CSV or Excel)
2. Analyses the data with pandas — net sales, returns, expenses per shop
3. Formats a report for Telegram and a template message for WhatsApp
4. Delivers both simultaneously to all configured recipients
5. Logs everything to a rotating file — so if it ever fails at 3 AM, you know why

---

## Architecture

```
main.py                      ← entry point, orchestrates the full pipeline
│
├── gmail_downloader.py      ← OAuth Gmail API → downloads Tally export → data/
├── data_processor.py        ← pandas analysis (sales, returns, expenses per shop)
├── formatters.py            ← builds Telegram message + WhatsApp parameters
├── telegram_sender.py       ← Telegram Bot API
├── whatsapp_sender.py       ← Meta WhatsApp Cloud API
├── ai_analyst.py            ← Claude API → generates plain-English insight
├── data_writer.py           ← persists JSON summaries for dashboard
│
├── config/
│   ├── settings.py          ← single config source (.env + client_config.yaml)
│   └── logger.py            ← rotating file logger (5 MB, 7 backups)
│
├── dashboard/
│   └── app.py               ← Streamlit dashboard
│
├── data/                    ← downloaded reports + JSON summaries (gitignored)
├── logs/                    ← automation.log (gitignored)
└── tests/                   ← 32 unit tests, no real credentials needed
```

**Data flow**

```
Gmail API → data/report.xlsx → pandas → summary dict ─┬→ Telegram
                                                        └→ WhatsApp
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.10+ |
| Data analysis | pandas |
| Email | Gmail API (OAuth 2.0) |
| Messaging | Telegram Bot API + Meta WhatsApp Cloud API |
| Config | python-dotenv + PyYAML |
| Logging | Python `logging` + `RotatingFileHandler` |
| Testing | pytest + pytest-cov (32 tests) |
| Scheduling | GitHub Actions (cron) |

---

## What Gets Sent

**Morning report (WhatsApp)**
```
📦 Sales Report — 24 Jun 2025

🏪 SHOP ONE        ₹3,50,000
🏪 SHOP TWO        ₹3,40,000
🏪 SHOP THREE      ₹3,55,000
🏪 SHOP FOUR       ₹3,55,000

📊 Total Net Sales  ₹14,00,000
💸 Total Expenses      ₹28,500
```
---

## Setup

### 1. Clone and install

```bash
git clone https://github.com/your-username/retail-report-automation.git
cd retail-report-automation
pip install -r requirements.txt
```

### 2. Set up credentials

```bash
cp .env.example .env
```

```ini
TELEGRAM_BOT_TOKEN=...     # from @BotFather on Telegram
TELEGRAM_CHAT_ID=...       # your group or channel ID
WHATSAPP_TOKEN=...         # Meta permanent token
WHATSAPP_PHONE_ID=...      # Meta phone number ID
```

### 3. Set up client config

```bash
cp client_config.example.yaml client_config.yaml
```

Edit `client_config.yaml` — add your shop names (order must match your WhatsApp template variables), recipient numbers, column names from your Tally export, and template names from Meta Business Manager.

### 4. Gmail OAuth (one-time)

```bash
python setup_gmail_auth.py
```

Opens a browser for Google authorisation. Saves `token.json` locally — gitignored.

### 5. Run

```bash
python main.py
```

Check `logs/automation.log` for a full trace.

---

## GitHub Actions — Fully Automated

The pipeline runs on GitHub's servers twice daily. No local machine needed.

```yaml
# Runs at 9:00 AM IST and 6:00 PM IST every day
on:
  schedule:
    - cron: "30 3 * * *"   # 9:00 AM IST
    - cron: "30 12 * * *"  # 6:00 PM IST
  workflow_dispatch:         # manual trigger from Actions tab
```

Sensitive files (`token.json`, `client_config.yaml`) are stored as base64-encoded GitHub Secrets and reconstructed at runtime. If any run fails, the bot sends a Telegram alert with a direct link to the logs.

---

## Tests

```bash
pytest -v                                    # run all 32 tests
pytest --cov=. --cov-report=term-missing     # with coverage
pytest tests/test_data_processor.py -v      # single file
```

No real credentials or business data needed — the test suite uses `tests/fixtures/test_config.yaml` with fictional values.

**What is tested**
- Net sales = gross sales minus returns (not just addition)
- Missing columns raise a descriptive error pointing to `client_config.yaml`
- Non-numeric amounts (blank cells, dashes) coerce to zero without crashing
- Morning template produces exactly 10 WhatsApp parameters
- Evening template produces exactly 5
- Morning/evening detection at the exact 15:00 IST boundary

---

## Logging

Every run appends to `logs/automation.log`. Rotates at 5 MB, keeps 7 backups.

```
2025-06-25 09:00:01 | INFO  | main              | Morning (full report) — 24 Jun 2025
2025-06-25 09:00:02 | INFO  | gmail_downloader  | Downloaded 'sales_yesterday.xlsx' → data/report.xlsx
2025-06-25 09:00:03 | INFO  | data_processor    | Analysis complete — net sales: 14,00,000 | expenses: 28,500
2025-06-25 09:00:04 | INFO  | telegram_sender   | Telegram delivered successfully
2025-06-25 09:00:05 | INFO  | whatsapp_sender   | Sent: 3 | Failed: 0
```

---

## Adding a New Client

This system is built to be client-agnostic. Every business-specific value lives in `client_config.yaml`.

To onboard a new business:
1. Create their `client_config.yaml` — shop names, phone numbers, Tally column names, WhatsApp template names
2. Run Gmail OAuth once with their account
3. Add their credentials as GitHub Secrets
4. Done — no Python files change

---

## Security

| File | GitHub | Why |
|---|---|---|
| `.env` | ❌ Gitignored | API tokens |
| `token.json` | ❌ Gitignored | Gmail OAuth credential |
| `client_config.yaml` | ❌ Gitignored | Business data and phone numbers |
| `data/` | ❌ Gitignored | Real sales figures |
| `logs/` | ❌ Gitignored | Financial totals in log lines |
| `.env.example` | ✅ Public | Placeholder values only |
| `client_config.example.yaml` | ✅ Public | Schema only, no real data |

---

## Author

**Vaibhav Chirania (https://github.com/vaibhav211134/shop-report-automation)** — CSE, IIT Kanpur 2025

Built this after coming back home and watching a 40-year-old business still do sales reporting manually every night. It now runs every day without anyone touching it.

If you run a retail business on Excel and want this set up — reach out.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/vaibhav-chirania-2a4094224/)
