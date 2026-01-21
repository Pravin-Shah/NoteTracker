# NoteTracker - Personal Knowledge & Task Management Ecosystem

A unified personal knowledge and task management system with two independent apps (TradeVault for trading insights, General for notes/tasks) sharing core infrastructure and a single database.

## Features

- **Notes**: Rich text notes with tags, importance, and attachments
- **Tasks**: Todo list with priority, due dates, recurring, and reminders
- **Trading Edges**: Create, edit, and search trading patterns with performance metrics
- **Prompts**: Reusable analysis templates with versioning
- **Calendar**: Event management and task calendar view
- **Reminders**: In-app, email, and Telegram notifications
- **Search**: Full-text search across all apps
- **Analytics**: Performance dashboards and insights

## Tech Stack

- **Frontend**: Streamlit 1.28.0
- **Backend**: Python 3.9+
- **Database**: SQLite (local, single file)
- **Scheduling**: APScheduler
- **Notifications**: Email, Telegram, In-app
- **Testing**: pytest, pytest-cov

## Project Structure

```
NoteTracker/
├── core/                    # Shared library (no UI logic)
├── apps/
│   ├── general/            # Notes + Tasks + Calendar App
│   ├── tradevault/         # Trading Edges + Prompts App
│   └── dashboard/          # Meta-Dashboard (Unified View)
├── tests/                  # Test suite
├── docs/                   # Documentation
├── data/                   # Database and uploads
└── logs/                   # Application logs
```

## Quick Start

### 1. Setup

```bash
cd C:\Users\shahp\Python\NoteTracker
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Initialize Database

```bash
python -c "from core.db import init_database; init_database()"
```

### 4. Run Tests

```bash
pytest --cov=core --cov=apps
```

### 5. Run Apps

```bash
# Terminal 1 - General App
streamlit run apps/general/streamlit_app.py

# Terminal 2 - TradeVault App
streamlit run apps/tradevault/streamlit_app.py

# Terminal 3 - Dashboard
streamlit run apps/dashboard/streamlit_app.py
```

## Development

### Code Standards
- Follow PEP 8
- Type hints on all functions
- Docstrings on all public functions
- All tests must pass

### Pre-commit Checklist
- [ ] All tests pass: `pytest --cov=core --cov=apps`
- [ ] Code formatted: `black .`
- [ ] Imports sorted: `isort .`
- [ ] No linting errors: `flake8 .`

### Testing

```bash
# All tests
pytest

# With coverage
pytest --cov=core --cov=apps --cov-report=html

# Specific test file
pytest tests/unit/test_db.py

# Integration tests only
pytest tests/integration/
```

## Documentation

- [Database Schema](docs/DATABASE.md)
- [Setup Guide](docs/SETUP.md)
- [Development](docs/DEVELOPMENT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API](docs/API.md)

## License

MIT License - See LICENSE file for details

## Version

1.0.0 (Development)

---

**For detailed documentation, see the PRD: COMPLETE_PRD_FINAL.md**
