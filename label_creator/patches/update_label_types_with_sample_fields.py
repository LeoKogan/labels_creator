import frappe


def execute():
    """
    Patch to update existing Label Type records with new sample and alignment fields
    This preserves all existing data and only adds missing fields with default values
    """
    update_existing_label_types()


def update_existing_label_types():
    """
    Update all existing Label Type records to include the new fields:
    - sku_sample
    - product_name_sample
    - sku_text_align
    - product_name_text_align
    """
    try:
        # Get all existing Label Type documents
        label_types = frappe.get_all("Label Type", fields=["name"])

        if not label_types:
            print("No Label Type records found to update")
            return

        updated_count = 0

        for lt in label_types:
            try:
                # Load the full document
                doc = frappe.get_doc("Label Type", lt.name)

                # Track if any changes were made
                modified = False

                # Add sku_sample if missing
                if not doc.get("sku_sample"):
                    doc.sku_sample = "SAM-PLE-SKU"
                    modified = True

                # Add product_name_sample if missing
                if not doc.get("product_name_sample"):
                    doc.product_name_sample = "Sample Product Name"
                    modified = True

                # Add sku_text_align if missing
                if not doc.get("sku_text_align"):
                    doc.sku_text_align = "Left"
                    modified = True

                # Add product_name_text_align if missing
                if not doc.get("product_name_text_align"):
                    doc.product_name_text_align = "Left"
                    modified = True

                # Save the document if any changes were made
                if modified:
                    doc.save(ignore_permissions=True)
                    updated_count += 1
                    print(f"Updated Label Type: {lt.name}")
                else:
                    print(f"Label Type already up to date: {lt.name}")

            except Exception as doc_error:
                print(f"Error updating Label Type {lt.name}: {str(doc_error)}")
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Label Type Update Error - {lt.name}"
                )
                continue

        frappe.db.commit()
        print(f"\nSuccessfully updated {updated_count} Label Type record(s)")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Label Type Update Patch Error")
        print(f"Error in update patch: {str(e)}")
        raise
