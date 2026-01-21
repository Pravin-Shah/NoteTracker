# Database Schema Documentation

## Overview

NoteTracker uses SQLite for data storage with a unified schema supporting all three apps:
- General App (Notes, Tasks, Calendar)
- TradeVault App (Edges, Prompts, Insights)
- Dashboard App (Meta-features)

## Core Tables

### users
- id: Primary Key
- username: Unique username
- password_hash: Hashed password
- email: User email
- telegram_id: Telegram chat ID (optional)
- created_date: Account creation timestamp
- is_active: Account status

### notifications
- id: Primary Key
- user_id: Foreign Key (users)
- app_name: 'tradevault' or 'general'
- notification_type: 'reminder', 'alert', 'update'
- title: Notification title
- message: Notification message
- is_read: Read status
- created_date: Notification timestamp

### global_tags
- id: Primary Key
- tag: Unique tag name
- category: Tag category ('trading', 'personal', 'work', 'health')
- usage_count: Number of times used
- created_date: Tag creation timestamp

## General App Tables

### gen_notes
- id: Primary Key
- user_id: Foreign Key (users)
- title: Note title
- content: Note content
- category: 'personal', 'work', 'financial', 'health', 'ideas'
- importance: 1-5 scale
- color: Visual categorization (optional)
- created_date: Creation timestamp
- last_updated: Last modification timestamp
- archived: Soft delete flag
- pinned: Pin status

### gen_tasks
- id: Primary Key
- user_id: Foreign Key (users)
- title: Task title
- description: Task description
- category: 'personal', 'work', 'financial', 'health'
- priority: 1-5 scale
- status: 'pending', 'in-progress', 'completed', 'cancelled'
- due_date: Due date (YYYY-MM-DD)
- due_time: Due time (HH:MM, optional)
- is_recurring: Recurring flag
- recurrence_pattern: 'daily', 'weekly', 'monthly' or cron format
- recurrence_end_date: Recurrence end date
- parent_task_id: Subtask hierarchy
- estimated_hours: Estimated time
- actual_hours_spent: Actual time spent
- archived: Soft delete flag
- created_date: Creation timestamp
- completed_date: Completion timestamp

### gen_events
- id: Primary Key
- user_id: Foreign Key (users)
- title: Event title
- description: Event description
- start_date: Event start date
- start_time: Event start time
- end_date: Event end date
- end_time: Event end time
- location: Event location
- is_all_day: All-day event flag
- category: 'personal', 'work', 'birthday', 'holiday'
- reminder_minutes_before: Reminder time

## TradeVault App Tables

### tv_edges
- id: Primary Key
- user_id: Foreign Key (users)
- title: Edge title
- category: 'grid', 'bias', 'pivot', 'MA-trail', 'volatility', 'reversal'
- strategy_id: Associated strategy
- timeframe: '1m', '5m', '15m', '30m', '1h', 'daily'
- market_condition: 'trending-up', 'ranging', 'volatile'
- instrument: Trading instrument
- description: Edge description
- status: 'active', 'testing', 'deprecated', 'hibernated'
- win_rate: Win rate percentage
- avg_points: Average profit per trade
- sample_size: Number of trades tested
- profit_factor: Total profit / Total loss
- confidence_grade: 'A', 'B', or 'C'
- risk_reward_ratio: Risk/reward ratio
- created_date: Creation timestamp
- last_updated: Last modification timestamp

### tv_prompts
- id: Primary Key
- user_id: Foreign Key (users)
- title: Prompt title
- category: 'analysis', 'debugging', 'hypothesis', 'research'
- content: Prompt content
- use_case: Intended use case
- expected_output: Expected output description
- version: Version string
- status: 'active', 'archived'
- created_date: Creation timestamp
- last_used_date: Last usage timestamp
- usage_count: Usage count
- is_favorite: Favorite flag

### tv_insights
- id: Primary Key
- user_id: Foreign Key (users)
- title: Insight title
- description: Insight description
- category: 'market-behavior', 'bias', 'psychology'
- date_observed: Observation date
- confidence_level: 'hypothesis', 'weak', 'moderate', 'strong'
- status: 'open', 'confirmed', 'disputed'

## Related Tables

### gen_note_tags
- note_id + tag: Primary Key (composite)
- Links notes to tags

### gen_task_tags
- task_id + tag: Primary Key (composite)
- Links tasks to tags

### tv_edge_tags
- edge_id + tag: Primary Key (composite)
- Links edges to tags

### gen_task_reminders
- id: Primary Key
- task_id: Foreign Key (gen_tasks)
- reminder_type: 'on-due-date', 'days-before', 'specific-time'
- reminder_value: Days or hour value
- reminder_time: Reminder time (HH:MM)
- is_sent: Sent flag
- sent_date: Send timestamp

### tv_edge_screenshots
- id: Primary Key
- edge_id: Foreign Key (tv_edges)
- file_path: Path to screenshot
- caption: Screenshot caption
- upload_date: Upload timestamp

## Indexes

Optimized indexes exist on:
- user_id (all tables for performance)
- status fields (for filtering)
- category fields (for grouping)
- created_date (for sorting)
- due_date/start_date (for calendar views)

## Data Relationships

```
users
├── gen_notes (1:M)
├── gen_tasks (1:M)
├── gen_events (1:M)
├── gen_task_reminders (1:M via gen_tasks)
├── tv_edges (1:M)
├── tv_prompts (1:M)
├── tv_insights (1:M)
└── notifications (1:M)
```

## Best Practices

1. Always use parameterized queries to prevent SQL injection
2. Use foreign keys to maintain referential integrity
3. Soft delete with 'archived' flag where applicable
4. Keep created_date and last_updated timestamps
5. Index frequently queried columns
6. Use transactions for multi-table operations

For implementation details, see `core/db.py`.
