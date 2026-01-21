# System Architecture

## High-Level Overview

NoteTracker is a unified personal knowledge management system with three independent web apps sharing a common backend:

```
┌─────────────────────────────────────────────────────────┐
│              Three Streamlit Applications               │
├─────────────────────────────────────────────────────────┤
│  General App    │  TradeVault App   │  Dashboard App   │
│  (Notes/Tasks)  │  (Edges/Prompts)  │  (Unified Home)  │
└────────┬────────┴────────┬──────────┴────────┬─────────┘
         │                 │                   │
         └─────────────────┼───────────────────┘
                           │
         ┌─────────────────▼─────────────────┐
         │      Core Library (Shared)        │
         │  ├─ Database Operations (db.py)   │
         │  ├─ Authentication (auth.py)      │
         │  ├─ Notifications (notify.py)     │
         │  ├─ Validation (validators.py)    │
         │  └─ UI Components (ui_comp.py)    │
         └──────────────────┬────────────────┘
                            │
         ┌──────────────────▼────────────────┐
         │    Single SQLite Database         │
         │   (data/shared_database.db)       │
         └──────────────────────────────────┘
```

## Architecture Layers

### 1. Presentation Layer (Streamlit)

**Three Independent Apps:**

- **General App** (`apps/general/`)
  - Pages: Dashboard, Notes, Tasks, Calendar, Search, Settings
  - Handles notes, tasks, calendar events, and reminders

- **TradeVault App** (`apps/tradevault/`)
  - Pages: Dashboard, Edges, Prompts, Insights, Search, Analytics, Settings
  - Handles trading edges, prompts, and performance tracking

- **Dashboard App** (`apps/dashboard/`)
  - Pages: Home (unified), Quick Add, Global Search
  - Provides meta-view across all apps

### 2. Business Logic Layer

**App-Specific Utilities:**

- `apps/general/utils/`
  - `note_ops.py`: Note CRUD operations
  - `task_ops.py`: Task CRUD and status management
  - `reminder_engine.py`: Reminder scheduling
  - `calendar_ops.py`: Calendar event management
  - `search.py`: Note/task search logic

- `apps/tradevault/utils/`
  - `edge_ops.py`: Edge CRUD and performance tracking
  - `prompt_ops.py`: Prompt versioning management
  - `insight_ops.py`: Insight management
  - `search.py`: Edge search logic
  - `analytics.py`: Performance calculations

### 3. Core Library Layer (Shared)

**Core Infrastructure** (`core/`)

- `db.py`: Database initialization and CRUD operations
  - Generic functions: `create_record()`, `update_record()`, `get_record()`, `search_records()`
  - Query execution: `execute_query()`, `execute_update()`
  - Connection management: `get_connection()`

- `auth.py`: User authentication
  - `register_user()`: New user registration
  - `login_user()`: Authentication
  - `get_current_user()`: Session management
  - Password hashing with SHA256

- `notifications.py`: Multi-channel notifications
  - `send_email()`: SMTP-based emails
  - `send_telegram()`: Telegram bot messages
  - `create_in_app_notification()`: Database notifications
  - `get_unread_notifications()`: Notification retrieval

- `validators.py`: Input validation
  - Email, date, time format validation
  - Priority, importance, confidence grade validation
  - File size validation

- `config.py`: Centralized configuration
  - File paths, database settings
  - Email/Telegram credentials (from .env)
  - File upload limits, logging settings

- `ui_components.py`: Reusable Streamlit widgets
  - `render_search_bar()`, `render_tag_selector()`
  - `render_priority_selector()`, `render_status_badge()`
  - `render_date_picker()`, `render_confirmation_modal()`

- `logger.py`: Logging setup
  - Rotating file handler (5MB max, 5 backups)
  - Console output with timestamps
  - Configurable log level

- `exceptions.py`: Custom exception hierarchy
  - `DatabaseError`, `ValidationError`, `AuthenticationError`
  - `NotificationError`, `FileUploadError`, `NotFoundError`

### 4. Data Layer

**Single SQLite Database** (`data/shared_database.db`)

- **User Management**: `users`, user sessions
- **General App**: `gen_notes`, `gen_tasks`, `gen_events`, `gen_task_reminders`, `gen_task_checklist`
- **TradeVault App**: `tv_edges`, `tv_prompts`, `tv_insights`, `tv_edge_screenshots`
- **Shared**: `notifications`, `global_tags`, `search_history`, `saved_searches`
- **Indexes**: On user_id, status, category, created_date, due_date for performance

## Data Flow Examples

### Creating a Note

```
1. General App (UI)
   └─ User clicks "New Note"

2. UI Handler (pages/02_Notes.py)
   └─ Collects title, content, category, tags

3. Note Ops (apps/general/utils/note_ops.py)
   └─ create_note(user_id, note_data)
     ├─ Validates input (validators.py)
     └─ Calls core.db.create_record()

4. Database (core/db.py)
   └─ INSERT INTO gen_notes
     └─ Returns note_id

5. Tag Management (apps/general/utils/note_ops.py)
   └─ add_note_tag(note_id, tag)

6. Result to UI
   └─ Display confirmation & redirect
```

### Checking Task Reminders

```
1. Reminder Engine (apps/general/utils/reminder_engine.py)
   └─ check_reminders() [runs every minute]

2. Query Database (core/db.py)
   └─ SELECT reminders WHERE is_sent = 0 AND due

3. For Each Reminder
   ├─ Create in-app notification (notifications.py)
   ├─ Send email (if configured)
   ├─ Send Telegram (if configured)
   └─ Mark as sent in database

4. User Sees Notification
   └─ On next app refresh or via Telegram/Email
```

### Global Search

```
1. Dashboard or App (pages/XX_Search.py)
   └─ User enters search query

2. Search Handler
   ├─ Call gen_apps search_notes() for General app results
   ├─ Call tradevault search_edges() for TradeVault results
   └─ Combine and sort results

3. Each Search Function
   └─ Execute SQL with LIKE pattern & filters

4. Results Displayed
   └─ User can click to view details
```

## Module Dependencies

```
apps/general/pages/
  ├─ imports: apps/general/utils/
  └─ imports: core/

apps/general/utils/
  ├─ imports: core/db, validators, notifications
  └─ imports: apps/general/utils/other_ops

core/
  ├─ db.py imports: config, exceptions, logger
  ├─ auth.py imports: db, validators
  ├─ notifications.py imports: db, config, logger
  └─ config.py imports: dotenv only

No circular imports - all dependencies flow downward
```

## Design Patterns

### 1. Repository Pattern
- Database operations isolated in `_ops.py` files
- Each module handles one entity type
- Clean separation from UI logic

### 2. Singleton Configuration
- Single `config.py` source for all settings
- Loaded once on app startup
- Used throughout via imports

### 3. Factory Pattern
- Generic CRUD functions in `core/db.py`
- Reused across all tables
- Reduces code duplication

### 4. Decorator Pattern
- `@require_login()` for authentication checks
- Streamlit functions decorated for permissions

## Scalability Considerations

### Current (MVP)
- Single SQLite database on disk
- No concurrency control (single user)
- Good for personal use

### Future Enhancements
- Multiple user support (with session management)
- PostgreSQL for production
- API layer (FastAPI) for multi-device sync
- Caching layer (Redis) for performance
- Async operations with APScheduler

## Performance Optimization

1. **Database Indexes**: On frequently queried columns
2. **Query Optimization**: Parameterized queries, efficient WHERE clauses
3. **Connection Pooling**: Reuse SQLite connections
4. **Lazy Loading**: Load related data only when needed
5. **Pagination**: Limit results for large datasets

## Security Measures

1. **Authentication**: SHA256 password hashing
2. **SQL Injection Prevention**: Parameterized queries
3. **XSS Prevention**: Streamlit auto-escapes
4. **Environment Variables**: Secrets in `.env`
5. **Access Control**: Per-user data filtering

## Testing Strategy

```
Unit Tests (tests/unit/)
├─ test_db.py: CRUD operations
├─ test_auth.py: Authentication
├─ test_validators.py: Input validation
└─ test_notifications.py: Notification sending

Integration Tests (tests/integration/)
├─ test_note_workflow.py: Create → Edit → Search
├─ test_task_workflow.py: Create → Remind → Complete
├─ test_edge_workflow.py: Create → Link → Analyze
└─ test_reminder_workflow.py: Schedule → Trigger → Send
```

## Configuration Management

1. **Development**: `.env` with DEBUG settings
2. **Testing**: In-memory SQLite database
3. **Production**: PostgreSQL with real secrets

## Deployment Options

1. **Local**: Standalone Streamlit app with SQLite
2. **Streamlit Cloud**: Free hosting (if no sensitive data)
3. **Docker**: Containerized with volume mounts
4. **Self-hosted**: Server with Python + Streamlit

---

For more details, see specific module documentation in `docs/` folder.
