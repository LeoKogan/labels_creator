#!/usr/bin/env python3
"""
Script to fix module cache issues in ERPNext for Label Creator app.
Run this from your bench directory using: bench --site [site-name] console

Then paste the commands below.
"""

import frappe

def fix_module_references():
    """Fix old module references in the database"""

    # Update Module Def table
    print("Checking Module Def table...")
    old_modules = frappe.db.sql("""
        SELECT name, module_name
        FROM `tabModule Def`
        WHERE module_name IN ('Consignor', 'Label Designer')
    """, as_dict=True)

    if old_modules:
        print(f"Found {len(old_modules)} old module references")
        frappe.db.sql("""
            UPDATE `tabModule Def`
            SET module_name='Label Creator'
            WHERE module_name IN ('Consignor', 'Label Designer')
        """)
        print("✓ Updated Module Def table")
    else:
        print("✓ No old modules in Module Def table")

    # Update Page table
    print("\nChecking Page table...")
    old_pages = frappe.db.sql("""
        SELECT name, module, title
        FROM `tabPage`
        WHERE module IN ('Consignor', 'Label Designer')
    """, as_dict=True)

    if old_pages:
        print(f"Found {len(old_pages)} pages with old module references")
        frappe.db.sql("""
            UPDATE `tabPage`
            SET module='Label Creator'
            WHERE module IN ('Consignor', 'Label Designer')
        """)
        print("✓ Updated Page table")
    else:
        print("✓ No old pages found")

    # Check current state
    print("\nCurrent Label Creator pages:")
    pages = frappe.db.sql("""
        SELECT name, module, title, page_name
        FROM `tabPage`
        WHERE name LIKE '%label%creator%' OR module='Label Creator'
    """, as_dict=True)

    for page in pages:
        print(f"  - {page.name} | Module: {page.module} | Title: {page.title}")

    # Commit changes
    frappe.db.commit()
    print("\n✓ All changes committed!")
    print("\nNext steps:")
    print("1. Exit console (type exit())")
    print("2. Run: bench clear-cache")
    print("3. Run: bench restart")

# Instructions to run in console
print("""
To fix module cache issues, run this in bench console:

bench --site [your-site-name] console

Then paste this command:
exec(open('apps/label_creator/fix_module_cache.py').read())
fix_module_references()
""")
