import frappe
from frappe import _
import os
import csv
import json
import qrcode
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph

@frappe.whitelist(allow_guest=False)
def upload_and_process(files_json):
    """
    Process uploaded CSV files and return product data
    """
    try:
        files_data = json.loads(files_json)
        aggregated_content = {}
        total_labels = 0

        for file_data in files_data:
            content = file_data.get('content', '')
            filename = file_data.get('filename', '')

            # Parse CSV content
            lines = content.strip().split('\n')
            reader = csv.reader(lines)
            header = next(reader, None)

            if not header:
                continue

            header_map = {col.strip(): idx for idx, col in enumerate(header)}

            # Process File Type 1: product, sku, quantity, display_price
            if {'product', 'sku', 'quantity', 'display_price'}.issubset(header_map):
                for row in reader:
                    try:
                        sku = row[header_map['sku']]
                        product = row[header_map['product']]
                        display_price = "{:.2f}".format(float(row[header_map['display_price']]))
                        quantity = int(row[header_map['quantity']])

                        if sku not in aggregated_content:
                            aggregated_content[sku] = {
                                "sku": sku,
                                "product": product,
                                "display_price": display_price,
                                "quantity": 0
                            }
                        aggregated_content[sku]["quantity"] += quantity
                        total_labels += quantity
                    except (ValueError, IndexError):
                        continue

            # Process File Type 2: name, sku, retail_price
            elif {'name', 'sku', 'retail_price'}.issubset(header_map):
                inventory_columns = [col for col in header if col.startswith('inventory_')]

                for row in reader:
                    try:
                        sku = row[header_map['sku']]
                        product_name = row[header_map['name']]
                        display_price = "{:.2f}".format(float(row[header_map['retail_price']]))
                        quantity = sum(
                            int(row[header_map[col]]) for col in inventory_columns
                            if col in header_map and row[header_map[col]].isdigit()
                        )

                        if sku not in aggregated_content:
                            aggregated_content[sku] = {
                                "sku": sku,
                                "product": product_name,
                                "display_price": display_price,
                                "quantity": 0
                            }
                        aggregated_content[sku]["quantity"] += quantity
                        total_labels += quantity
                    except (ValueError, IndexError):
                        continue

        processed_content = list(aggregated_content.values())

        return {
            "success": True,
            "processed_content": processed_content,
            "total_labels": total_labels
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Label Creator Upload Error")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist(allow_guest=False)
def generate_labels(label_type, processed_content_json):
    """
    Generate PDF labels and return file path
    """
    try:
        from label_creator.utils.label_generator import create_labels_pdf

        processed_content = json.loads(processed_content_json)

        # Generate PDF
        pdf_path = create_labels_pdf(processed_content, label_type)

        # Get filename
        filename = os.path.basename(pdf_path)

        # Create proper file URL for Frappe
        # Files in public/files are accessible via /files/
        file_url = f"/files/label_creator/{filename}"

        return {
            "success": True,
            "file_url": file_url,
            "filename": filename
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Label Creator Generation Error")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist(allow_guest=False)
def get_label_types():
    """
    Get available label types from DocType
    """
    try:
        # Get all Label Type documents
        label_types_list = frappe.get_all(
            "Label Type",
            fields=["*"],
            order_by="label_type_name"
        )

        # Convert to dictionary format for compatibility
        label_types = {}
        for lt in label_types_list:
            label_types[lt.label_type_name] = {
                "name": lt.display_name,
                "label_width": lt.label_width,
                "label_height": lt.label_height,
                "labels_per_row": lt.labels_per_row,
                "labels_per_column": lt.labels_per_column,
                "label_orientation": lt.label_orientation or "portrait",
                "page_width_inch": lt.page_width_inch,
                "page_height_inch": lt.page_height_inch,
                "margin_top": lt.margin_top or 0,
                "margin_bottom": lt.margin_bottom or 0,
                "margin_left": lt.margin_left or 0,
                "margin_right": lt.margin_right or 0,
                "qrcode_x_offset": lt.qrcode_x_offset or 0,
                "qrcode_y_offset": lt.qrcode_y_offset or 0,
                "qrcode_size_pts": lt.qrcode_size_pts or None,
                "sku_x_offset": lt.sku_x_offset or 0,
                "sku_y_offset": lt.sku_y_offset or 0,
                "price_x_offset": lt.price_x_offset or 0,
                "price_y_offset": lt.price_y_offset or 0,
                "price_rotation": lt.price_rotation or 0,
                "show_product_name": lt.show_product_name or 0,
                "file_name": lt.file_name or "labels"
            }

        return {
            "success": True,
            "label_types": label_types
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Label Creator Get Types Error")
        return {
            "success": False,
            "message": str(e)
        }
