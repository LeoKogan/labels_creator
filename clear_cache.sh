#!/bin/bash

# Clear Frappe Cache Script for Label Creator
# Run this script to clear all caches and force reload of web pages

echo "==========================================="
echo "Label Creator - Clear Cache Script"
echo "==========================================="
echo ""

# Check if we're in a bench directory
if [ ! -d "apps/label_creator" ] && [ ! -d "../label_creator" ]; then
    echo "ERROR: This script must be run from:"
    echo "  - The frappe-bench directory, OR"
    echo "  - The label_creator app directory"
    echo ""
    echo "Current directory: $(pwd)"
    exit 1
fi

# Navigate to bench directory if we're in the app directory
if [ -d "../label_creator" ]; then
    cd ../..
fi

echo "Step 1: Clearing Frappe cache..."
bench clear-cache

echo ""
echo "Step 2: Clearing website cache..."
bench clear-website-cache

echo ""
echo "Step 3: Building assets..."
bench build

echo ""
echo "Step 4: Restarting bench..."
bench restart

echo ""
echo "==========================================="
echo "✅ Cache cleared successfully!"
echo "==========================================="
echo ""
echo "Next steps:"
echo "1. Open your browser"
echo "2. Clear browser cache (Ctrl+Shift+Delete or Cmd+Shift+Delete)"
echo "3. Hard refresh the Label Creator page (Ctrl+Shift+R or Cmd+Shift+R)"
echo "4. You should now see:"
echo "   - Preview column in the table"
echo "   - Version footer: 'Label Creator v2.5.0 | Last Updated: 2026-01-05'"
echo ""
