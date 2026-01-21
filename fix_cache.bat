@echo off
echo Fixing TypeScript/Vite cache issues...
cd frontend

echo.
echo Step 1: Clearing node_modules/.vite cache...
if exist node_modules\.vite (
    rmdir /s /q node_modules\.vite
    echo Cache cleared!
) else (
    echo No cache found.
)

echo.
echo Step 2: Restarting dev server...
echo Please run: npm run dev
echo.
pause
