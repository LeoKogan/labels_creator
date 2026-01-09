# Label Creator - Installation Instructions

## Installing Python Dependencies

The Label Creator app requires the `python-barcode` package for generating multiple barcode formats (QR Code, Code 39, Code 128, EAN-13, EAN-8, UPC-A).

### For Frappe/ERPNext Environment

Run the following commands on your Frappe server:

```bash
# Navigate to your bench directory
cd ~/frappe-bench  # or wherever your bench is located

# Install the app's dependencies
bench pip install -e apps/label_creator

# Or install python-barcode directly
bench pip install python-barcode

# Restart bench to load the new modules
bench restart
```

### Alternative: Install Manually

If you don't have access to `bench` commands, install directly:

```bash
# Activate your Frappe virtual environment first
source ~/frappe-bench/env/bin/activate

# Install python-barcode
pip install python-barcode>=0.15.1

# Deactivate and restart your web server
deactivate
sudo systemctl restart nginx  # or your web server
sudo supervisorctl restart all  # or your process manager
```

### Verify Installation

Test that the module is installed correctly:

```bash
# Navigate to bench
cd ~/frappe-bench

# Run bench console
bench --site your-site-name console

# In the console, test:
import barcode
from barcode.writer import ImageWriter
print("barcode module loaded successfully")
```

### After Installation

1. Clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)
2. Refresh the Label Creator page
3. Check the footer - you should see "Label Creator v2.5.0 | Last Updated: 2026-01-05"
4. Test the preview functionality

## Troubleshooting

If you still get "No module named 'barcode'" error:

1. **Check which Python is running Frappe:**
   ```bash
   bench --site your-site-name console
   import sys
   print(sys.executable)
   ```

2. **Install in the correct environment:**
   Make sure you're installing in the same Python environment that Frappe is using.

3. **Check if it's installed:**
   ```bash
   bench pip list | grep barcode
   ```
   You should see `python-barcode` in the list.

4. **Restart everything:**
   ```bash
   bench restart
   sudo supervisorctl restart all
   ```

## Dependencies List

The app requires these Python packages (all listed in setup.py):
- frappe
- qrcode>=7.4.2
- python-barcode>=0.15.1
- Pillow>=10.0.0
- reportlab>=4.0.4
- PyMuPDF>=1.23.0

All of these should be installed automatically when you run `bench pip install -e apps/label_creator`.
