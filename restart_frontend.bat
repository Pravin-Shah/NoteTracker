@echo off
echo Restarting Frontend with Fresh Build...
echo.

cd frontend

echo Step 1: Clearing Vite cache...
if exist node_modules\.vite (
    rmdir /s /q node_modules\.vite
    echo Cache cleared!
) else (
    echo No cache found.
)

echo.
echo Step 2: Stopping any running dev servers...
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Step 3: Starting dev server...
npm run dev
