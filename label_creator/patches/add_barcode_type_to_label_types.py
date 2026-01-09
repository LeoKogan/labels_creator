import frappe


def execute():
    """
    Patch to add barcode_type field to existing Label Type records
    Sets default value to "QR Code" for backwards compatibility
    """
    add_barcode_type_to_existing_label_types()


def add_barcode_type_to_existing_label_types():
    """
    Update all existing Label Type records to include the barcode_type field
    Default: "QR Code" (maintains existing functionality)
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

                # Add barcode_type if missing
                if not doc.get("barcode_type"):
                    doc.barcode_type = "QR Code"
                    doc.save(ignore_permissions=True)
                    updated_count += 1
                    print(f"Updated Label Type: {lt.name} - Set barcode_type to 'QR Code'")
                else:
                    print(f"Label Type already has barcode_type: {lt.name}")

            except Exception as doc_error:
                print(f"Error updating Label Type {lt.name}: {str(doc_error)}")
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Barcode Type Update Error - {lt.name}"
                )
                continue

        frappe.db.commit()
        print(f"\nSuccessfully updated {updated_count} Label Type record(s)")

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Add Barcode Type Patch Error")
        print(f"Error in barcode type patch: {str(e)}")
        raise
