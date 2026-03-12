# ChatGPT Account Creator Bot

An automated ChatGPT account creation tool built with **Python 3.8+**, Playwright
browser automation, SQLite storage, and an optional FastAPI REST server.

---

## Project structure

```
chatgpt-account-creator/
├── requirements.txt          Python dependencies
├── .env.example              Environment variable template
├── main.py                   CLI entry point
├── config.py                 Configuration (reads .env)
├── core/
│   ├── account_creator.py    Browser-automation flow
│   └── email_manager.py      Email generation & inbox polling
├── database/
│   └── db_manager.py         SQLite account & log storage
├── utils/
│   └── logger.py             Rotating-file + coloured console logger
├── api/
│   └── server.py             FastAPI REST server
├── cli/
│   ├── create_account.py     CLI – single account
│   └── create_batch.py       CLI – batch accounts
├── data/                     SQLite database files (git-ignored)
└── logs/                     Log files (git-ignored)
```

---

## Requirements

* Python 3.8+
* Google Chrome / Chromium (installed automatically by Playwright)

---

## Setup

```bash
# 1. Clone
git clone https://github.com/Khontol54/chatgpt-account-creator.git
cd chatgpt-account-creator

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Install Playwright browser
playwright install chromium

# 5. Configure environment
cp .env.example .env
# Edit .env with your preferred settings
```

---

## Usage

### Single account

```bash
python main.py --single
```

### Batch accounts

```bash
python main.py --batch 5
```

### Interactive mode

```bash
python main.py
```

### CLI helpers

```bash
python cli/create_account.py
python cli/create_batch.py 3
```

### REST API server

```bash
python api/server.py
# or
uvicorn api.server:app --host 0.0.0.0 --port 3000
```

#### API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/create-account` | Create single account |
| POST | `/api/create-batch` | Create batch (`{"count": N}`) |
| GET | `/api/accounts` | List all accounts |
| GET | `/api/accounts/{email}` | Get account by email |

---

## Configuration

All settings are controlled via environment variables (see `.env.example`).

| Variable | Default | Description |
|----------|---------|-------------|
| `HEADLESS` | `true` | Run browser in headless mode |
| `EMAIL_PROVIDER` | `tempmail` | `tempmail` / `gmail` / `custom` |
| `RATE_LIMIT_PER_DAY` | `5` | Max accounts per day |
| `DELAY_BETWEEN` | `60` | Seconds between creations |
| `DB_PATH` | `./data/accounts.db` | SQLite database path |
| `LOG_LEVEL` | `INFO` | Logging level |
| `PROXY_ENABLED` | `false` | Enable proxy support |
| `PORT` | `3000` | API server port |

---

## Database schema

**accounts**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| email | TEXT | Account email (unique) |
| password | TEXT | Account password |
| status | TEXT | `pending` / `created` / `failed` |
| verified | INTEGER | `1` if email-verified |
| created_at | TEXT | ISO 8601 timestamp |
| updated_at | TEXT | ISO 8601 timestamp |
| last_login | TEXT | ISO 8601 timestamp |
| notes | TEXT | Free-form notes |

**logs**

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| account_id | INTEGER | FK → accounts.id |
| action | TEXT | Action name |
| status | TEXT | `success` / `failed` / `pending` |
| timestamp | TEXT | ISO 8601 timestamp |
| details | TEXT | Extra information |

---

## License

MIT
