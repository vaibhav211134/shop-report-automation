<div align="center">

# 📦 Retail Report Automation

**A production-grade pipeline that automatically analyses Tally ERP exports and delivers daily sales reports to WhatsApp and Telegram — zero manual effort.**

Built for a 40-year-old family clothing business in Bihar running 4 shops.
Now saves 30 minutes every day and has eliminated manual reporting entirely.

## The Problem

Every evening, someone in the family had to manually pull numbers from Tally, calculate net sales across 4 shops, and type it into a WhatsApp group. This took 30 minutes, happened at the end of a long day, and was prone to errors.

This system replaced that entirely.

---

# 🚀 What It Does

The pipeline runs **twice every day** on its own via **GitHub Actions** — no server, no manual trigger.

### ⏰ Automation Schedule

| Time | Report Type | Key Metrics |
| :---: | :---: | :---: |
| **11:00 AM** | 📅 Full Yesterday Report | Net Sales + Expenses + Totals |
| **7:00 PM** | ⚡ Today's Sales Flash | Net Sales + Running Totals |

<br />

### 🔄 The Execution Pipeline
*Each run follows a precise 5-step workflow:*

**1. 📥 Automated Ingestion** Connects to Gmail and downloads the latest Tally exports (CSV or Excel).

**2. 📊 Data Analysis** Analyzes the data with `pandas` — calculating net sales, returns, and expenses per shop.

**3. ✍️ Dynamic Formatting** Formats a rich report for Telegram and a structured template message for WhatsApp.

**4. 📲 Instant Delivery** Delivers both reports simultaneously to all configured recipients.

**5. 📁 Resilient Logging** Logs everything to a rotating file — so if it ever fails at 3 AM, you know why.

---

## Architecture

| File | Purpose |
|---|---|
| `main.py` | Entry point — orchestrates the full pipeline |
| `gmail_downloader.py` | OAuth Gmail API → downloads Tally export → `data/` |
| `data_processor.py` | pandas analysis — net sales, returns, expenses per shop |
| `formatters.py` | Builds Telegram message + WhatsApp parameters |
| `telegram_sender.py` | Sends via Telegram Bot API |
| `whatsapp_sender.py` | Sends via Meta WhatsApp Cloud API |
| `ai_analyst.py` | Claude API → generates plain-English daily insight |
| `data_writer.py` | Persists JSON summaries for the dashboard |
| `config/settings.py` | Single config source — loads `.env` + `client_config.yaml` |
| `config/logger.py` | Rotating file logger (5 MB per file, 7 backups) |
| `dashboard/app.py` | Streamlit dashboard |
| `data/` | Downloaded reports + JSON summaries — gitignored |
| `logs/` | `automation.log` — gitignored |
| `tests/` | 32 unit tests, no real credentials needed |

## 📊 Data Flow

```mermaid
graph LR
    A["📧 Gmail API"] -->|Download| B["📁 data/report.xlsx"]
    B -->|Process| C["🐼 pandas"]
    C -->|Aggregate| D["📦 summary_dict"]
    D --> E["🔵 Telegram"]
    D --> F["🟢 WhatsApp"]

    %% Styling for better visuals
    style A fill:#ea4335,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#150458,stroke:#333,stroke-width:2px,color:#fff
    style E fill:#0088cc,stroke:#333,color:#fff
    style F fill:#25D366,stroke:#333,color:#fff
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

# ⚙️ Setup & Configuration

Follow these steps to get the automation pipeline running in your local environment.

---

### 1️. Clone and Install
First, bring the repository to your machine and install the necessary dependencies.

```bash
git clone [https://github.com/your-username/retail-report-automation.git](https://github.com/your-username/retail-report-automation.git)
cd retail-report-automation
pip install -r requirements.txt
```

### 2. Set up credentials

```bash
cp .env.example .env
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

# 🚀 Scalability: Onboarding a New Business

The architecture is strictly **client-agnostic**. All business-specific logic is decoupled from the core engine, meaning the pipeline can be scaled to new retail chains in minutes with **zero code changes**.

---

### 🛠️ The 4-Step Onboarding Process

**1. Define Business Logic**
Populate the `client_config.yaml` with the new business's metadata:
*Shop names, recipient phone numbers, Tally column mappings, and WhatsApp template IDs.*

**2. Authentication Handshake**
Run the Gmail OAuth flow once using the new client’s credentials to generate a secure `token.json`.

**3. Secure Secret Injection**
Upload the encoded configuration and tokens as **GitHub Secrets**.

**4. Instant Activation**
The system is live. The GitHub Action will now pick up the new configuration and start delivering reports immediately.

<br />

| Feature | Implementation |
| :--- | :--- |
| **Logic Separation** | 100% YAML-based |
| **Code Changes** | **None** required |
| **Deployment Time** | < 5 Minutes |

> [!TIP]
> **Zero-Touch Maintenance:** Because the core Python files remain untouched during onboarding, there is no risk of introducing regressions when adding new businesses to the pipeline.

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
