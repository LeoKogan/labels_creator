import frappe


def execute():
    """
    Patch to create default label types for existing installations
    """
    create_default_label_types()


def create_default_label_types():
    """
    Create default label type configurations
    """
    try:
        default_label_types = [
            {
                "label_type_name": "DYMO-30333 | S-14052",
                "display_name": "DYMO 30333 - Small Multipurpose",
                "label_width": 0.5,
                "label_height": 1.0,
                "labels_per_row": 2,
                "labels_per_column": 5,
                "label_orientation": "portrait",
                "page_width_inch": 8.5,
                "page_height_inch": 11.0,
                "margin_top": 0.5,
                "margin_bottom": 0.5,
                "margin_left": 0.5,
                "margin_right": 0.5,
                "offset_input_mode": "Percentage",
                "show_qr_code": 1,
                "qrcode_x_offset": 0.05,
                "qrcode_x_offset_pct": 10,
                "qrcode_y_offset": 0.05,
                "qrcode_y_offset_pct": 5,
                "show_sku": 1,
                "sku_x_offset": 0.05,
                "sku_x_offset_pct": 10,
                "sku_y_offset": 0.45,
                "sku_y_offset_pct": 45,
                "sku_font_type": "Helvetica",
                "sku_font_size": 7,
                "sku_max_word_length": 9,
                "show_product_name": 0,
                "product_name_x_offset": 0.05,
                "product_name_x_offset_pct": 10,
                "product_name_y_offset": 0.6,
                "product_name_y_offset_pct": 60,
                "product_name_font_type": "Helvetica",
                "product_name_font_size": 6,
                "product_name_max_word_length": 9,
                "show_price": 1,
                "price_x_offset": 0.05,
                "price_x_offset_pct": 10,
                "price_y_offset": 0.8,
                "price_y_offset_pct": 80,
                "price_rotation": 0,
                "price_font_type": "Helvetica-Bold",
                "price_font_size": 8,
                "file_name": "labels"
            },
            {
                "label_type_name": "S-18475",
                "display_name": "S-18475 - Landscape Label",
                "label_width": 2.0,
                "label_height": 1.0,
                "labels_per_row": 3,
                "labels_per_column": 8,
                "label_orientation": "landscape",
                "page_width_inch": 8.5,
                "page_height_inch": 11.0,
                "margin_top": 0.5,
                "margin_bottom": 0.5,
                "margin_left": 0.5,
                "margin_right": 0.5,
                "offset_input_mode": "Percentage",
                "show_qr_code": 1,
                "qrcode_x_offset": 0.1,
                "qrcode_x_offset_pct": 5,
                "qrcode_y_offset": 0.05,
                "qrcode_y_offset_pct": 5,
                "show_sku": 1,
                "sku_x_offset": 1.0,
                "sku_x_offset_pct": 50,
                "sku_y_offset": 0.1,
                "sku_y_offset_pct": 10,
                "sku_font_type": "Helvetica",
                "sku_font_size": 7,
                "sku_max_word_length": 9,
                "show_product_name": 1,
                "product_name_x_offset": 1.0,
                "product_name_x_offset_pct": 50,
                "product_name_y_offset": 0.3,
                "product_name_y_offset_pct": 30,
                "product_name_font_type": "Helvetica",
                "product_name_font_size": 6,
                "product_name_max_word_length": 9,
                "show_price": 1,
                "price_x_offset": 1.8,
                "price_x_offset_pct": 90,
                "price_y_offset": 0.5,
                "price_y_offset_pct": 50,
                "price_rotation": 90,
                "price_font_type": "Helvetica-Bold",
                "price_font_size": 10,
                "file_name": "labels"
            }
        ]

        for label_type_data in default_label_types:
            if not frappe.db.exists("Label Type", label_type_data["label_type_name"]):
                doc = frappe.get_doc({
                    "doctype": "Label Type",
                    **label_type_data
                })
                doc.insert(ignore_permissions=True)
                print(f"Created default label type: {label_type_data['label_type_name']}")
            else:
                print(f"Label type already exists: {label_type_data['label_type_name']}")

        frappe.db.commit()

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Label Type Creation Patch Error")
        raise
