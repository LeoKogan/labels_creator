#!/usr/bin/env python3
"""
Label Creator - Installation Verification Script
Run this script to verify all dependencies are installed correctly
"""

import sys
import os

def check_module(module_name, import_path=None):
    """Check if a Python module is installed"""
    try:
        if import_path:
            __import__(import_path)
        else:
            __import__(module_name)
        print(f"✅ {module_name}: Installed")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: NOT installed - {str(e)}")
        return False

def main():
    print("=" * 60)
    print("Label Creator - Installation Verification")
    print("=" * 60)
    print()

    # Check Python version
    print(f"Python Version: {sys.version}")
    print(f"Python Path: {sys.executable}")
    print()

    # Check required modules
    print("Checking Required Dependencies:")
    print("-" * 60)

    all_ok = True

    # Core dependencies
    all_ok &= check_module("frappe")
    all_ok &= check_module("qrcode")
    all_ok &= check_module("python-barcode", "barcode")
    all_ok &= check_module("Pillow", "PIL")
    all_ok &= check_module("reportlab")
    all_ok &= check_module("PyMuPDF", "fitz")

    print()
    print("-" * 60)

    # Verify barcode module functionality
    if check_module("python-barcode", "barcode"):
        print()
        print("Testing barcode module functionality:")
        print("-" * 60)
        try:
            import barcode
            from barcode.writer import ImageWriter

            # Test available barcode types
            available_types = [
                'code39', 'code128', 'ean13', 'ean8', 'upca'
            ]

            for barcode_type in available_types:
                try:
                    barcode.get_barcode_class(barcode_type)
                    print(f"  ✅ {barcode_type.upper()}: Available")
                except Exception as e:
                    print(f"  ❌ {barcode_type.upper()}: Error - {str(e)}")
                    all_ok = False

            print("  ✅ ImageWriter: Available")

        except Exception as e:
            print(f"  ❌ Barcode module test failed: {str(e)}")
            all_ok = False

    print()
    print("=" * 60)

    if all_ok:
        print("✅ ALL DEPENDENCIES INSTALLED CORRECTLY!")
        print()
        print("Next steps:")
        print("1. Run: bench migrate")
        print("2. Run: bench restart")
        print("3. Clear browser cache and reload Label Creator page")
        return 0
    else:
        print("❌ SOME DEPENDENCIES ARE MISSING!")
        print()
        print("To install missing dependencies, run:")
        print()
        print("  cd ~/frappe-bench")
        print("  bench pip install python-barcode qrcode Pillow reportlab PyMuPDF")
        print("  bench restart")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
