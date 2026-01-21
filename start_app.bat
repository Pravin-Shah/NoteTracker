@echo off
cd /d "C:\Users\shahp\Python\NoteTracker"
python -m streamlit run pages/home.py --logger.level=error
pause
