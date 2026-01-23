"""
Initialize habits tracking database tables.
Run this once to create the tables.
"""

from api.database import get_db_connection

def init_habits_tables():
    """Create habits tracking tables if they don't exist."""

    with get_db_connection() as conn:
        # Daily logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                log_date DATE NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(user_id, log_date)
            )
        """)

        # Exercise entries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS exercise_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_log_id INTEGER NOT NULL,
                exercise_type TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                duration_minutes INTEGER,
                reps INTEGER,
                notes TEXT,
                FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
            )
        """)

        # Meal entries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_log_id INTEGER NOT NULL,
                meal_type TEXT NOT NULL,
                completed INTEGER DEFAULT 0,
                quality TEXT,
                portion_size TEXT,
                has_protein INTEGER DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
            )
        """)

        # Water entries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS water_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_log_id INTEGER NOT NULL,
                glasses INTEGER DEFAULT 0,
                FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
            )
        """)

        # Sleep entries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sleep_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                daily_log_id INTEGER NOT NULL,
                completed INTEGER DEFAULT 0,
                hours REAL DEFAULT 0,
                quality TEXT,
                energy TEXT,
                FOREIGN KEY (daily_log_id) REFERENCES daily_logs(id) ON DELETE CASCADE
            )
        """)

        # Create indexes
        conn.execute("CREATE INDEX IF NOT EXISTS idx_daily_logs_user_date ON daily_logs(user_id, log_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_exercise_entries_log ON exercise_entries(daily_log_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_meal_entries_log ON meal_entries(daily_log_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sleep_entries_log ON sleep_entries(daily_log_id)")

        print("Habits tables created successfully!")

if __name__ == "__main__":
    init_habits_tables()
