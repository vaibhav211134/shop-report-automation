<div align="center">

# Retail Report Automation

A production pipeline that pulls daily Tally ERP exports from Gmail, analyses sales across all shops, and delivers formatted reports to WhatsApp and Telegram — automatically, twice a day.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-Analysis-150458?style=flat-square&logo=pandas&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Scheduled-2088FF?style=flat-square&logo=githubactions&logoColor=white)
![Tests](https://img.shields.io/badge/Tests-32_passing-2ea44f?style=flat-square)
![WhatsApp](https://img.shields.io/badge/WhatsApp-Meta_Cloud_API-25D366?style=flat-square&logo=whatsapp&logoColor=white)

</div>

---

## The problem it solves

My family has run a clothing business in Bihar for 40 years — 4 shops, and every evening someone was manually pulling numbers from Excel and typing them into WhatsApp. 30 minutes of work, every day, for decades.

This system replaced that entirely. It now runs on its own before anyone wakes up.

---

## How it works

GitHub Actions triggers the pipeline twice daily. No server. No manual steps.

| Run | Time | What it sends |
|---|---|---|
| Morning | 11:00 AM IST | Full report of yesterday — net sales, expenses, totals per shop |
| Evening | 7:00 PM IST | Sales flash for today so far — net sales per shop + running total |

Each run: downloads the Tally export from Gmail → analyses with pandas → formats → delivers to Telegram and WhatsApp simultaneously → logs everything.

---

## Architecture

| File | Role |
|---|---|
| `main.py` | Orchestrator — runs the full pipeline |
| `gmail_downloader.py` | OAuth Gmail API → downloads Tally export |
| `data_processor.py` | pandas — net sales, returns, expenses per shop |
| `formatters.py` | Builds Telegram message + WhatsApp parameters |
| `telegram_sender.py` | Telegram Bot API |
| `whatsapp_sender.py` | Meta WhatsApp Cloud API |
| `config/settings.py` | Single config source — `.env` + `client_config.yaml` |
| `config/logger.py` | Rotating file logger — 5 MB, 7 backups |
| `tests/` | 32 unit tests, no real credentials needed |

**Data flow**

```
Gmail API → Tally export → pandas → summary
                                      ├── Telegram
                                      ├── WhatsApp
```

---

## What the report looks like

```
📦 Sales Report — 24 Jun 2025

🏪 SHOP ONE      ₹3,50,000
🏪 SHOP TWO      ₹3,40,000
🏪 SHOP THREE    ₹3,55,000
🏪 SHOP FOUR     ₹3,55,000
--------------------------------

📊 Total Net Sales   ₹14,00,000
💸 Total Expenses       ₹28,500

```

---

## Setup

```bash
git clone https://github.com/vaibhav211134/shop-report-automation.git
cd shop-report-automation
pip install -r requirements.txt
```

```bash
cp .env.example .env                          # add your API tokens
cp client_config.example.yaml client_config.yaml   # add shop names + numbers
python setup_gmail_auth.py                    # one-time Gmail OAuth
python main.py                                # run
```

Full credentials guide in `.env.example` and `client_config.example.yaml`.

---

## Automated via GitHub Actions

```yaml
on:
  schedule:
    - cron: "30 3 * * *"    # 9:00 AM IST
    - cron: "30 12 * * *"   # 6:00 PM IST
  workflow_dispatch:          # manual trigger anytime
```

`token.json` and `client_config.yaml` are stored as base64-encoded GitHub Secrets and reconstructed at runtime. If a run fails, the bot sends a Telegram alert with a direct link to the logs.

---

## Tests

```bash
pytest -v
pytest --cov=. --cov-report=term-missing
```

The test suite uses fictional data in `tests/fixtures/test_config.yaml` — no real credentials needed. Covers net sales calculation, missing column handling, non-numeric coercion, WhatsApp parameter counts, and morning/evening boundary detection.

---

## Adding a new client

Everything business-specific lives in `client_config.yaml`. To onboard a new business — create their config file, run Gmail OAuth once, add secrets to GitHub. No Python files change.

---

## Security

`.env`, `token.json`, `client_config.yaml`, `data/`, and `logs/` are all gitignored. Only `.example` files with placeholder values are public.

---

<div align="center">

Built by **[Vaibhav Chirania](https://www.linkedin.com/in/vaibhav-chirania-2a4094224/)** — CSE, IIT Kanpur 2025

If you run a retail business on Excel and want this set up, reach out.

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Vaibhav_Chirania-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/vaibhav-chirania-2a4094224/)

</div>
