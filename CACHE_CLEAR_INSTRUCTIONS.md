# Clear Cache Instructions - Label Creator

## Problem
You're not seeing the updated Label Creator page with:
- ❌ Preview column in the table
- ❌ Version footer showing "v2.5.0"

This is a **caching issue** - Frappe is serving an old cached version of the page.

---

## Solution - Clear ALL Caches

### Option 1: Use the Automated Script (Easiest)

1. **Copy the script to your server:**
   ```bash
   # From your local machine, copy to server
   scp clear_cache.sh your-user@your-server:/home/frappe/frappe-bench/
   ```

2. **Run on your Frappe server:**
   ```bash
   cd ~/frappe-bench
   chmod +x clear_cache.sh
   ./clear_cache.sh
   ```

### Option 2: Manual Commands

Run these commands **on your Frappe server** where the bench is installed:

```bash
# Navigate to bench directory
cd ~/frappe-bench

# Clear all Frappe caches
bench clear-cache

# Clear website cache specifically
bench clear-website-cache

# Build assets (JavaScript/CSS)
bench build

# Restart bench to reload everything
bench restart
```

### Option 3: Via Frappe UI

1. Login to your Frappe/ERPNext as Administrator
2. Go to: **Awesome Bar (Ctrl+K)** → Search for "Clear Cache"
3. Click **"Reload"** or **"Clear Cache"**
4. Click **"Clear Website Cache"**

---

## After Clearing Server Cache

### Clear Browser Cache

Even after clearing server cache, your **browser** may still cache the old page.

**Hard Refresh:**
- **Windows/Linux**: Press `Ctrl + Shift + R` or `Ctrl + F5`
- **Mac**: Press `Cmd + Shift + R`

**Or Clear All Browser Cache:**
- **Windows/Linux**: Press `Ctrl + Shift + Delete`
- **Mac**: Press `Cmd + Shift + Delete`
- Select "Cached images and files"
- Click "Clear data"

**Or Use Incognito/Private Mode:**
- Open a new incognito/private window
- Navigate to the Label Creator page
- This bypasses all browser cache

---

## Verify It Worked

After clearing caches and refreshing, you should see:

✅ **At the bottom of the page:**
```
Label Creator v2.5.0 | Last Updated: 2026-01-05 | Barcode Support: QR Code, Code 39, Code 128, EAN-13, EAN-8, UPC-A
```

✅ **In the table header:**
```
☑️  |  Preview  |  SKU  |  Product  |  Price  |  Quantity
```

✅ **Preview images loading** in the Preview column for each product row

---

## Still Not Working?

If you still don't see the changes after clearing all caches:

### 1. Check the file is updated on server
```bash
cd ~/frappe-bench/apps/label_creator
git pull origin claude/fix-sku-hyphen-breaking-AOb9W
grep -n "v2.5.0" label_creator/www/label-creator.html
```
You should see the version string in the output.

### 2. Check for build errors
```bash
cd ~/frappe-bench
bench build --verbose
```
Look for any errors in the output.

### 3. Check console for errors
Open browser Developer Tools (F12) → Console tab
Look for any JavaScript errors in red.

### 4. Force rebuild
```bash
cd ~/frappe-bench
rm -rf sites/assets/*
bench build --force
bench restart
```

### 5. Check if python-barcode is installed
```bash
cd ~/frappe-bench
bench pip list | grep barcode
```
Should show: `python-barcode    0.16.1` (or similar)

If not installed:
```bash
bench pip install python-barcode
bench restart
```

---

## Quick Checklist

- [ ] Pulled latest code from git
- [ ] Installed python-barcode (`bench pip install python-barcode`)
- [ ] Cleared Frappe cache (`bench clear-cache`)
- [ ] Cleared website cache (`bench clear-website-cache`)
- [ ] Built assets (`bench build`)
- [ ] Restarted bench (`bench restart`)
- [ ] Cleared browser cache (Ctrl+Shift+R or Cmd+Shift+R)
- [ ] Verified footer shows "v2.5.0"
- [ ] Verified Preview column appears in table

---

## Contact

If none of these solutions work, please provide:
1. Output of `bench version`
2. Screenshot of the page
3. Browser console errors (F12 → Console tab)
4. Output of `bench pip list | grep -E "barcode|qrcode|reportlab"`
