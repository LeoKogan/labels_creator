import frappe


def execute():
    """
    Patch to update existing Label Type records with new QR code size fields
    Converts old qrcode_size_pts to new qrcode_size_inch/qrcode_size_pct fields
    """
    update_qr_code_size_fields()


def update_qr_code_size_fields():
    """
    Update all existing Label Type records to include the new fields:
    - qrcode_size_inch
    - qrcode_size_pct
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

                # Set default qrcode_size_pct if using Percentage mode and field is missing
                offset_mode = doc.get("offset_input_mode") or "Percentage"
                if offset_mode == "Percentage":
                    if not doc.get("qrcode_size_pct"):
                        doc.qrcode_size_pct = 40.0  # Default 40% of label width
                        modified = True
                else:  # Inches mode
                    # Leave qrcode_size_inch blank for auto-calculation
                    pass

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
                    f"Label Type QR Size Update Error - {lt.name}"
                )
                continue

        frappe.db.commit()
        print(f"\nSuccessfully updated {updated_count} Label Type record(s)")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Label Type QR Size Update Patch Error")
        print(f"Error in update patch: {str(e)}")
        raise
