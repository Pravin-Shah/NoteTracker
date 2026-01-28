# Deployment Plan - January 29, 2026

This plan covers the deployment of recent changes including:
1.  **Rich Text Editor Upgrade** (TipTap).
2.  **File Attachment Fixes** (PDF/Text support).
3.  **Daily Tracker & Habits Features** (Database tables).

## ⚠️ Pre-Deployment Checks
- [ ] Ensure you have the SSH private key: `C:\Users\shahp\Downloads\ssh-key-2026-01-21.key`
- [ ] Ensure you have committed all changes locally.

---

## 🚀 Step 1: Backup Production Database
**Crucial Step**: Before touching anything, create a backup.

1.  SSH into the server:
    ```bash
    ssh -i "C:\Users\shahp\Downloads\ssh-key-2026-01-21.key" ubuntu@80.225.231.148
    ```

2.  Run the backup script manually:
    ```bash
    ~/backup_db.sh
    ```
    *Verify the backup was created:*
    ```bash
    ls -l ~/backups/
    # You should see a new file like shared_database_2026-01-29_XXXX.db
    ```

---

## 📥 Step 2: Update Codebase

1.  Navigate to project directory:
    ```bash
    cd ~/notetracker
    ```

2.  Pull the latest changes:
    ```bash
    git pull
    ```

---

## 🛠️ Step 3: Frontend Update (Critical)
We added new packages (`@tiptap/react`, etc.), so `npm install` is **mandatory**.

1.  Go to frontend directory:
    ```bash
    cd frontend
    ```

2.  Install new dependencies:
    ```bash
    npm install
    ```

3.  Build the frontend:
    ```bash
    npm run build
    ```

4.  Fix permissions (if needed for Nginx):
    ```bash
    chmod -R 755 dist
    ```

---

## 🗄️ Step 4: Database Migrations
We need to add new columns for attachments and create tables for habits.

1.  Return to root directory:
    ```bash
    cd ~/notetracker
    ```

2.  Activate virtual environment:
    ```bash
    source venv/bin/activate
    ```

3.  **Migration 1: Add Attachment Columns** (Safe to run multiple times):
    ```bash
    python api/migrate_attachments.py
    ```
    *Output should say "Migration completed successfully!" or "columns already exist".*

4.  **Migration 2: Backfill Old Data** (Fixes "broken" look for existing files):
    ```bash
    python api/backfill_attachments.py
    ```
    *Output should list updated attachments or say 0 found.*

5.  **Migration 3: Create Habits Tables** (Safe to run multiple times):
    ```bash
    python api/init_habits_db.py
    ```
    *Output should say "Habits tables created successfully!".*

---

## 🔄 Step 5: Restart Services

1.  Restart the backend service:
    ```bash
    # If using systemd (Recommended):
    sudo systemctl restart notetracker
    
    # OR if running manually with nohup:
    pkill -f uvicorn
    nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
    ```

2.  Reload Nginx (to serve new frontend assets):
    ```bash
    sudo systemctl reload nginx
    ```

---

## ✅ Step 6: Verification

1.  Visit the app: [http://80-225-231-148.nip.io](http://80-225-231-148.nip.io)
2.  **Test "New Note"**: Click "New Note" -> Editor should be blank (TipTap).
3.  **Test Attachments**: Open a note with images. Hover over image -> Check "Open/Download" buttons.
4.  **Test Habits**: If Habits UI is visible, check if it loads without error.

## 🆘 Rollback Plan (If things go wrong)
If the database is corrupted or app fails:

1.  **Restore Database**:
    ```bash
    # Stop backend
    sudo systemctl stop notetracker
    
    # Copy backup back
    cp ~/backups/shared_database_[TIMESTAMP].db ~/notetracker/data/shared_database.db
    
    # Start backend
    sudo systemctl start notetracker
    ```
