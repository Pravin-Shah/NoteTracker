# NoteTracker Deployment Guide

## Server Details
- **Server**: Oracle Cloud VM (Ubuntu)
- **IP**: 80.225.231.148
- **Domain**: 80-225-231-148.nip.io
- **SSH Key**: `C:\Users\shahp\Downloads\ssh-key-2026-01-21.key`

---

## Quick Deployment (After Code Changes)

### Step 1: Push changes from Windows
```powershell
cd C:\Users\shahp\Python\NoteTracker
git add .
git commit -m "Your change description"
git push
```

### Step 2: Deploy on Server
```bash
# SSH into server
ssh -i "C:\Users\shahp\Downloads\ssh-key-2026-01-21.key" ubuntu@80.225.231.148

# Pull and rebuild
cd ~/notetracker
git pull
cd frontend && npm run build && chmod -R 755 dist
sudo systemctl reload nginx
```

---

## Full Setup (First Time Deployment)

### Prerequisites on Server
- Ubuntu 20.04+
- Node.js 18+
- Python 3.10+
- Nginx
- SQLite3

### 1. Clone Repository
```bash
cd ~
git clone https://github.com/Pravin-Shah/NoteTracker.git notetracker
cd notetracker
```

### 2. Backend Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << 'EOF'
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://80-225-231-148.nip.io,http://80.225.231.148
EOF

# Initialize database
python -c "import sys; sys.path.insert(0, '.'); from core.db import init_database; init_database()"

# Add Google OAuth columns (if not exists)
sqlite3 data/shared_database.db "ALTER TABLE users ADD COLUMN google_id TEXT;"
sqlite3 data/shared_database.db "ALTER TABLE users ADD COLUMN avatar_url TEXT;"
```

### 3. Frontend Setup
```bash
cd ~/notetracker/frontend

# Create .env file
cat > .env << 'EOF'
VITE_API_URL=http://80-225-231-148.nip.io/api
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
EOF

# Install and build
npm install
npm run build
chmod -R 755 dist
```

### 4. Nginx Configuration
```bash
sudo nano /etc/nginx/sites-available/notetracker
```

Paste this config:
```nginx
server {
    listen 80;
    server_name 80.225.231.148 80-225-231-148.nip.io;

    # Frontend - serve static files
    location / {
        root /home/ubuntu/notetracker/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API - proxy to backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Uploads - serve static files
    location /uploads/ {
        alias /home/ubuntu/notetracker/data/uploads/;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/notetracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Start Backend (Background)
```bash
cd ~/notetracker
source venv/bin/activate
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
```

### 6. (Optional) Create Systemd Service for Backend
```bash
sudo nano /etc/systemd/system/notetracker.service
```

Paste:
```ini
[Unit]
Description=NoteTracker Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/notetracker
Environment="PATH=/home/ubuntu/notetracker/venv/bin"
ExecStart=/home/ubuntu/notetracker/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable notetracker
sudo systemctl start notetracker
```

---

## Troubleshooting

### Check if backend is running
```bash
curl http://localhost:8000/api/health
```

### View backend logs
```bash
tail -50 ~/notetracker/uvicorn.log
# or if using systemd:
sudo journalctl -u notetracker -f
```

### Check nginx logs
```bash
sudo tail -50 /var/log/nginx/error.log
```

### Restart services
```bash
# Restart backend
pkill -f uvicorn
cd ~/notetracker && source venv/bin/activate
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &

# or if using systemd:
sudo systemctl restart notetracker

# Restart nginx
sudo systemctl restart nginx
```

### Database location
```
~/notetracker/data/shared_database.db
```

### Fix permissions after deployment
```bash
chmod -R 755 ~/notetracker/frontend/dist
```

---

## Backup

### Automatic Daily Backups (Already Configured)

The server has an automatic backup system configured via cron that runs daily at 2 AM UTC.

**Backup Script Location**: `~/backup_db.sh`

**Backup Directory**: `~/backups/`

**Retention Policy**: Last 7 days of backups are kept (older backups auto-deleted)

### Check Existing Backups
```bash
ls -la ~/backups/
```

### View Backup Logs
```bash
cat ~/backups/backup.log
```

### Manual Backup (Run Anytime)
```bash
# Run the backup script manually
~/backup_db.sh

# Or copy with custom timestamp
cp ~/notetracker/data/shared_database.db ~/backups/shared_database_$(date +%Y-%m-%d_%H%M).db
```

### Backup uploads (manual)
```bash
tar -czf ~/backups/uploads_$(date +%Y%m%d).tar.gz ~/notetracker/data/uploads/
```

### Restore from Backup
```bash
# Stop the backend first
pkill -f uvicorn

# Copy backup to database location
cp ~/backups/shared_database_YYYY-MM-DD_HHMM.db ~/notetracker/data/shared_database.db

# Restart the backend
cd ~/notetracker && source venv/bin/activate
nohup python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
```

### Cron Job Configuration (Reference)
The backup cron job is already set up. To view or modify:
```bash
# View current cron jobs
crontab -l

# Edit cron jobs (if needed)
crontab -e

# Current schedule: 0 2 * * * (daily at 2 AM UTC)
```

### Backup Script Contents (Reference)
```bash
#!/bin/bash
# ~/backup_db.sh
BACKUP_DIR="/home/ubuntu/backups"
DB_PATH="/home/ubuntu/notetracker/data/shared_database.db"
DATE=$(date +%Y-%m-%d_%H%M)

cp "$DB_PATH" "$BACKUP_DIR/shared_database_$DATE.db"
find "$BACKUP_DIR" -name "shared_database_*.db" -mtime +7 -delete
echo "[$(date)] Backup completed: shared_database_$DATE.db"
```

---

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Go to APIs & Services → Credentials
4. Create OAuth 2.0 Client ID
5. Add authorized JavaScript origins:
   - `http://80-225-231-148.nip.io`
   - `http://80.225.231.148`
6. Add authorized redirect URIs:
   - `http://80-225-231-148.nip.io`
7. Copy Client ID to frontend `.env` file

---

## File Structure on Server
```
~/notetracker/
├── api/                 # Backend API
├── core/                # Core modules
├── frontend/
│   ├── dist/            # Built frontend (served by nginx)
│   └── src/             # Frontend source
├── data/
│   ├── shared_database.db
│   └── uploads/
├── venv/                # Python virtual environment
├── .env                 # Backend environment variables
└── uvicorn.log          # Backend logs
```
