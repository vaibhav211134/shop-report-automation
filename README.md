# Shop Report Automation

Production-grade modular reporting pipeline for:
- Gmail attachment download
- Pandas report aggregation
- Telegram delivery
- WhatsApp template delivery

## Entry Point

Run the complete pipeline only via:

```bash
python main.py
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill credentials.
4. Copy `client_config.example.yaml` to `client_config.yaml` for shop order and numbers.
5. Ensure `token.json` exists (use existing `get_token.py` flow).

## Tests

Run tests without real API keys:

```bash
pytest -q
```

Fixtures are in `tests/fixtures/test_config.yaml`.
