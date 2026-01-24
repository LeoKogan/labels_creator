import frappe
from frappe import _


def after_install():
    """
    Setup Label Creator after installation
    """
    create_page_if_not_exists()
    create_default_label_types()
    update_existing_label_types()


def update_existing_label_types():
    """
    Update all existing Label Type records to include new sample and alignment fields
    This can be called manually via bench console if needed
    """
    try:
        # Get all existing Label Type documents
        label_types = frappe.get_all("Label Type", fields=["name"])

        if not label_types:
            frappe.logger().info("No Label Type records found to update")
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
                    doc.sku_text_align = "Centre"
                    modified = True

                # Add product_name_text_align if missing
                if not doc.get("product_name_text_align"):
                    doc.product_name_text_align = "Left"
                    modified = True

                # Add price_sample if missing
                if not doc.get("price_sample"):
                    doc.price_sample = 29.99
                    modified = True

                # Add currency if missing
                if not doc.get("currency"):
                    doc.currency = "CAD"
                    modified = True

                # Save the document if any changes were made
                if modified:
                    doc.save(ignore_permissions=True)
                    updated_count += 1
                    frappe.logger().info(f"Updated Label Type: {lt.name}")

            except Exception as doc_error:
                frappe.logger().error(f"Error updating Label Type {lt.name}: {str(doc_error)}")
                frappe.log_error(
                    frappe.get_traceback(),
                    f"Label Type Update Error - {lt.name}"
                )
                continue

        frappe.db.commit()
        frappe.logger().info(f"Successfully updated {updated_count} Label Type record(s)")

    except Exception as e:
        frappe.logger().error(f"Error updating Label Types: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Label Type Update Error")


def create_page_if_not_exists():
    """
    Ensure the Label Creator page exists
    """
    try:
        if not frappe.db.exists("Page", "label-creator"):
            frappe.logger().info("Label Creator page will be created from page definition")
        else:
            frappe.logger().info("Label Creator page already exists")

    except Exception as e:
        frappe.logger().error(f"Error checking Label Creator page: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Label Creator Installation Error")


def create_default_label_types():
    """
    Create default label type configurations
    """
    try:
        default_label_types = [
            {
                "label_type_name": "SAMPLE S-18475",
                "display_name": "SAMPLE DYMO-30299 | Uline S-18475 | Jewelry (3/8 x 3/4)",
                "label_width": 2.9,
                "label_height": 0.44,
                "labels_per_row": 1,
                "labels_per_column": 2,
                "label_orientation": "landscape",
                "page_width_inch": 2.95,
                "page_height_inch": 0.9,
                "margin_top": 0.0,
                "margin_bottom": 0.0,
                "margin_left": 0.0,
                "margin_right": 0.0,
                "offset_input_mode": "Percentage",
                "show_qr_code": 1,
                "qrcode_x_offset": 0.058,
                "qrcode_x_offset_pct": 2.0,
                "qrcode_y_offset": 0.066,
                "qrcode_y_offset_pct": 15.0,
                "qrcode_size_inch": 0.35,
                "qrcode_size_pct": 40.0,
                "show_sku": 1,
                "sku_sample": "SAM-PLE-SKU",
                "sku_x_offset": 0.435,
                "sku_x_offset_pct": 15.0,
                "sku_y_offset": 0.154,
                "sku_y_offset_pct": 35.0,
                "sku_font_type": "Helvetica",
                "sku_font_size": 9,
                "sku_max_word_length": 4,
                "sku_text_align": "Left",
                "show_product_name": 1,
                "product_name_sample": "Sample Product Name",
                "product_name_x_offset": 2.175,
                "product_name_x_offset_pct": 75.0,
                "product_name_y_offset": 0.022,
                "product_name_y_offset_pct": 5.0,
                "product_name_font_type": "Helvetica",
                "product_name_font_size": 8,
                "product_name_max_word_length": 12,
                "product_name_text_align": "Left",
                "show_price": 1,
                "price_sample": 29.99,
                "currency": "USD",
                "price_x_offset": 2.755,
                "price_x_offset_pct": 95.0,
                "price_y_offset": 0.22,
                "price_y_offset_pct": 50.0,
                "price_rotation": 90,
                "price_font_type": "Helvetica-Bold",
                "price_font_size": 10,
                "file_name": "label_S-18475"
            },
            {
                "label_type_name": "SAMPLE S-16987",
                "display_name": "SAMPLE Uline S-16987 (1/2 x 1)",
                "label_width": 0.5,
                "label_height": 1.0,
                "labels_per_row": 16,
                "labels_per_column": 10,
                "label_orientation": "portrait",
                "page_width_inch": 8.5,
                "page_height_inch": 11.0,
                "margin_top": 0.5,
                "margin_bottom": 0.5,
                "margin_left": 0.244,
                "margin_right": 0.244,
                "offset_input_mode": "Percentage",
                "show_qr_code": 1,
                "qrcode_x_offset": 0.05,
                "qrcode_x_offset_pct": 10.0,
                "qrcode_y_offset": 0.05,
                "qrcode_y_offset_pct": 5.0,
                "qrcode_size_inch": 0.35,
                "qrcode_size_pct": 40.0,
                "show_sku": 1,
                "sku_sample": "SAM-PLE-SKU",
                "sku_x_offset": 0.05,
                "sku_x_offset_pct": 10.0,
                "sku_y_offset": 0.45,
                "sku_y_offset_pct": 45.0,
                "sku_font_type": "Helvetica",
                "sku_font_size": 6,
                "sku_max_word_length": 0,
                "sku_text_align": "Left",
                "show_product_name": 0,
                "product_name_sample": "Sample Product Name",
                "product_name_x_offset": 0.05,
                "product_name_x_offset_pct": 10.0,
                "product_name_y_offset": 0.6,
                "product_name_y_offset_pct": 60.0,
                "product_name_font_type": "Helvetica",
                "product_name_font_size": 5,
                "product_name_max_word_length": 0,
                "product_name_text_align": "Left",
                "show_price": 1,
                "price_sample": 29.99,
                "currency": "USD",
                "price_x_offset": 0.05,
                "price_x_offset_pct": 10.0,
                "price_y_offset": 0.8,
                "price_y_offset_pct": 80.0,
                "price_rotation": 0,
                "price_font_type": "Helvetica-Bold",
                "price_font_size": 8,
                "file_name": "label_S-16987"
            },
            {
                "label_type_name": "SAMPLE DYMO-30333 | S-14052",
                "display_name": "SAMPLE Dymo 30333 or S-14052 (1/2 x 1)",
                "label_width": 0.5,
                "label_height": 1.0,
                "labels_per_row": 2,
                "labels_per_column": 1,
                "label_orientation": "portrait",
                "page_width_inch": 1.0,
                "page_height_inch": 1.0,
                "margin_top": 0.0,
                "margin_bottom": 0.0,
                "margin_left": 0.0,
                "margin_right": 0.0,
                "offset_input_mode": "Percentage",
                "show_qr_code": 1,
                "qrcode_x_offset": 0.05,
                "qrcode_x_offset_pct": 10.0,
                "qrcode_y_offset": 0.05,
                "qrcode_y_offset_pct": 5.0,
                "qrcode_size_inch": 0.35,
                "qrcode_size_pct": 40.0,
                "show_sku": 1,
                "sku_sample": "SAM-PLE-SKU",
                "sku_x_offset": 0.05,
                "sku_x_offset_pct": 10.0,
                "sku_y_offset": 0.45,
                "sku_y_offset_pct": 45.0,
                "sku_font_type": "Helvetica",
                "sku_font_size": 7,
                "sku_max_word_length": 7,
                "sku_text_align": "Left",
                "show_product_name": 0,
                "product_name_sample": "Sample Product Name",
                "product_name_x_offset": 0.05,
                "product_name_x_offset_pct": 10.0,
                "product_name_y_offset": 0.6,
                "product_name_y_offset_pct": 60.0,
                "product_name_font_type": "Helvetica",
                "product_name_font_size": 6,
                "product_name_max_word_length": 10,
                "product_name_text_align": "Left",
                "show_price": 1,
                "price_sample": 29.99,
                "currency": "USD",
                "price_x_offset": 0.05,
                "price_x_offset_pct": 10.0,
                "price_y_offset": 0.8,
                "price_y_offset_pct": 80.0,
                "price_rotation": 0,
                "price_font_type": "Helvetica-Bold",
                "price_font_size": 8,
                "file_name": "label_30333"
            }
        ]

        for label_type_data in default_label_types:
            if not frappe.db.exists("Label Type", label_type_data["label_type_name"]):
                doc = frappe.get_doc({
                    "doctype": "Label Type",
                    **label_type_data
                })
                doc.insert(ignore_permissions=True)
                frappe.logger().info(f"Created default label type: {label_type_data['label_type_name']}")
            else:
                frappe.logger().info(f"Label type already exists: {label_type_data['label_type_name']}")

        frappe.db.commit()

    except Exception as e:
        frappe.logger().error(f"Error creating default label types: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Label Type Creation Error")

