# Setup & Installation Guide

## Prerequisites

- Python 3.9 or higher
- Git
- pip (Python package manager)

## Installation Steps

### 1. Clone the Repository

```bash
cd C:\Users\shahp\Python
git clone <repository-url> NoteTracker
cd NoteTracker
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

For development, also install dev dependencies:

```bash
pip install -r requirements-dev.txt
```

### 4. Configure Environment

Copy the environment template and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```
DATABASE_PATH=data/shared_database.db
LOG_LEVEL=DEBUG

# Optional: Telegram notifications
TELEGRAM_TOKEN=your_token_here

# Optional: Email notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
```

### 5. Initialize Database

```bash
python -c "from core.db import init_database; init_database()"
```

This creates `data/shared_database.db` with all required tables.

### 6. Run Tests

```bash
pytest --cov=core --cov=apps
```

All tests should pass. Check coverage at `htmlcov/index.html`.

### 7. Run the Apps

Open three terminal windows and run:

**Terminal 1 - General App (Notes, Tasks)**
```bash
streamlit run apps/general/streamlit_app.py
# Opens at http://localhost:8501
```

**Terminal 2 - TradeVault App (Trading Edges)**
```bash
streamlit run apps/tradevault/streamlit_app.py
# Opens at http://localhost:8502
```

**Terminal 3 - Dashboard (Unified View)**
```bash
streamlit run apps/dashboard/streamlit_app.py
# Opens at http://localhost:8503
```

## Verification

After setup, verify everything works:

1. ✅ Database initialized
   ```bash
   ls -lh data/shared_database.db
   ```

2. ✅ Tests pass
   ```bash
   pytest -v
   ```

3. ✅ Apps start without errors
   - Check each Streamlit app in browser
   - You can log in with test credentials

4. ✅ Create a test note
   - Go to General App
   - Create a new note
   - Verify it's saved in database

5. ✅ Check logs
   ```bash
   tail logs/app.log
   ```

## Troubleshooting

### Port Already in Use

If port 8501/8502/8503 is in use, specify a different port:

```bash
streamlit run apps/general/streamlit_app.py --server.port 8504
```

### Database Locked

Close all app connections and restart:

```bash
# Stop all Streamlit apps (Ctrl+C)
# Delete database (if needed)
rm data/shared_database.db
# Reinitialize
python -c "from core.db import init_database; init_database()"
```

### Module Import Errors

Reinstall dependencies with --force-reinstall:

```bash
pip install --force-reinstall -r requirements.txt
```

### Permission Denied (Linux/macOS)

Make scripts executable:

```bash
chmod +x setup.sh
./setup.sh
```

### Test Failures

Run tests with verbose output to diagnose:

```bash
pytest -v tests/
```

## Directory Structure After Setup

```
NoteTracker/
├── .env                              # Configuration (gitignored)
├── data/
│   ├── shared_database.db            # SQLite database
│   └── uploads/
│       ├── general/
│       └── tradevault/
├── logs/
│   └── app.log                       # Application logs
└── venv/                             # Virtual environment
```

## Next Steps

1. Read [DEVELOPMENT.md](DEVELOPMENT.md) for coding guidelines
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
3. Check [DATABASE.md](DATABASE.md) for schema details
4. See main [README.md](../README.md) for feature overview

## Getting Help

- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- Review test files in `tests/` for usage examples
- Check PRD document for detailed specifications

---

**Setup complete!** You're ready to start development. 🚀
