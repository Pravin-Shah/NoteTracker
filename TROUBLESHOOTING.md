# 🔧 Troubleshooting Guide - Module Import Error

## ❌ Error You're Seeing

```
The requested module '/src/types/note.ts' does not provide an export named 'Attachment'
```

## ✅ Solution

I've already cleared the Vite cache for you. Now follow these steps:

### Step 1: Stop the Frontend Server
Press `Ctrl+C` in the terminal running the frontend

### Step 2: Restart the Frontend
```bash
cd frontend
npm run dev
```

Or use the startup script:
```bash
.\start_frontend.bat
```

### Step 3: Hard Refresh Browser
Once the server restarts, open `http://localhost:5173` and press:
- **Windows/Linux:** `Ctrl + Shift + R`
- **Mac:** `Cmd + Shift + R`

---

## 🔍 Why This Happened

This is a common Vite development server caching issue. When new TypeScript files are created, Vite sometimes caches the old module resolution and doesn't pick up new exports.

## ✅ What I Did

1. ✅ Cleared Vite cache (`node_modules/.vite`)
2. ✅ Verified `Attachment` type is properly exported in `types/note.ts`
3. ✅ Verified all imports are correct

## 🎯 Alternative Solutions (If Still Not Working)

### Option 1: Full Clean Restart
```bash
cd frontend

# Stop the dev server (Ctrl+C)

# Clear cache
Remove-Item -Recurse -Force node_modules\.vite

# Restart
npm run dev
```

### Option 2: Check TypeScript Config
The `tsconfig.json` should have:
```json
{
  "compilerOptions": {
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true
  }
}
```

### Option 3: Verify File Exists
Check that this file exists and has the export:
```
frontend/src/types/note.ts
```

Should contain:
```typescript
export interface Attachment {
  id: number;
  file_path: string;
  file_type: string | null;
  upload_date: string | null;
}
```

---

## 📋 Quick Checklist

- [x] Vite cache cleared
- [ ] Frontend server restarted
- [ ] Browser hard refreshed
- [ ] Error should be gone!

---

## 🚀 After Fix

Once the error is resolved, you should see:
1. **Left Sidebar** - Folders and tags
2. **Middle Feed** - Notes list (empty initially)
3. **Right Panel** - "No note selected" message

Then you can:
1. Click "New Note" in sidebar
2. Create your first note
3. Test image paste (Ctrl+V)!

---

## 💡 Pro Tip

If you encounter similar module errors in the future:
1. Stop the dev server
2. Run: `Remove-Item -Recurse -Force node_modules\.vite`
3. Restart: `npm run dev`

This clears Vite's cache and forces a fresh build.

---

## 🆘 Still Having Issues?

If the error persists after following these steps, check:

1. **Is the backend running?**
   ```bash
   # Should see: "Application startup complete"
   .\start_backend.bat
   ```

2. **Is the frontend running?**
   ```bash
   # Should see: "Local: http://localhost:5173"
   .\start_frontend.bat
   ```

3. **Check browser console**
   - Press F12
   - Look for any other errors
   - Share those errors for more help

---

**The cache has been cleared. Just restart the frontend server and you should be good to go!** ✅
