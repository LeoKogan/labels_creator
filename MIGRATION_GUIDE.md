# Label Creator - Migration Guide

## Updating Existing Label Types with New Fields

This guide explains how to update existing Label Type records to include the new sample and alignment fields that were added in the latest version.

### New Fields Added

The following fields were added to the Label Type doctype:
- `sku_sample`: Sample SKU text for visualization (default: "SAM-PLE-SKU")
- `product_name_sample`: Sample product name for visualization (default: "Sample Product Name")
- `sku_text_align`: Text alignment for SKU (Left/Centre/Right)
- `product_name_text_align`: Text alignment for Product Name (Left/Centre/Right)

### Automatic Migration

The migration will run automatically when you:
1. Install the app for the first time
2. Run `bench migrate`

The migration script will:
- Preserve all existing data in your Label Type records
- Add the new fields with default values only if they don't exist
- Skip records that already have the new fields

### Manual Migration

If you need to run the migration manually, you can use the Frappe bench console:

```bash
# Enter the bench console
bench --site [your-site-name] console

# Run the migration function
from label_creator.install.install import update_existing_label_types
update_existing_label_types()
```

### What Gets Updated

For each existing Label Type record:
- If `sku_sample` is missing → set to "SAM-PLE-SKU"
- If `product_name_sample` is missing → set to "Sample Product Name"
- If `sku_text_align` is missing → set to "Left"
- If `product_name_text_align` is missing → set to "Left"

### Verification

After running the migration, you can verify the updates by:

1. **Via UI**:
   - Go to Label Type list
   - Open any Label Type record
   - Check the SKU and Product Name tabs for the new fields

2. **Via Console**:
   ```bash
   bench --site [your-site-name] console

   import frappe
   lt = frappe.get_doc("Label Type", "YOUR-LABEL-TYPE-NAME")
   print(f"SKU Sample: {lt.sku_sample}")
   print(f"Product Name Sample: {lt.product_name_sample}")
   print(f"SKU Text Align: {lt.sku_text_align}")
   print(f"Product Name Text Align: {lt.product_name_text_align}")
   ```

### Customizing Sample Values

After migration, you can customize the sample values for each Label Type:

1. Open the Label Type record in ERPNext
2. Go to the **SKU** tab
3. Update the "Sample SKU (for visualization)" field
4. Go to the **Product Name** tab
5. Update the "Sample Product Name (for visualization)" field
6. Save the record

These sample values will be used in the label preview to help you visualize how your labels will look.

### Rollback

If you need to rollback the changes:

```bash
bench --site [your-site-name] console

import frappe

# Clear the new fields from all Label Types
label_types = frappe.get_all("Label Type", fields=["name"])
for lt in label_types:
    doc = frappe.get_doc("Label Type", lt.name)
    doc.sku_sample = None
    doc.product_name_sample = None
    doc.sku_text_align = None
    doc.product_name_text_align = None
    doc.save(ignore_permissions=True)

frappe.db.commit()
```

### Troubleshooting

**Issue**: Migration fails with permission error
- **Solution**: Run the migration as Administrator user or ensure your role has full permissions on Label Type doctype

**Issue**: Fields are not visible in the UI
- **Solution**:
  1. Clear cache: `bench --site [your-site-name] clear-cache`
  2. Reload the page
  3. Check that the Label Type doctype has been migrated: `bench --site [your-site-name] migrate`

**Issue**: Preview still shows old sample values
- **Solution**:
  1. Clear browser cache
  2. Hard reload the page (Ctrl+Shift+R or Cmd+Shift+R)
  3. Verify the sample values are saved in the Label Type record

### Support

If you encounter any issues during migration, please:
1. Check the Error Log in ERPNext (Settings > Error Log)
2. Review the migration logs in `logs/bench.log`
3. Open an issue on the GitHub repository with the error details
