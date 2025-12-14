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


@frappe.whitelist(allow_guest=False)
def preview_label(label_type_config_json):
    """
    Generate a preview image of label page based on configuration
    """
    try:
        import io
        import base64
        from label_creator.utils.label_generator import draw_label, get_or_create_qr
        from reportlab.lib.units import inch

        # Try to import PyMuPDF for PDF to image conversion
        try:
            import fitz  # PyMuPDF
            has_pymupdf = True
        except ImportError:
            has_pymupdf = False

        # Parse the configuration
        config = json.loads(label_type_config_json)

        # Sample data for preview
        sample_data = {
            'sku': 'SAMPLE-123',
            'product': 'Sample Product',
            'display_price': '29.99'
        }

        # Get page and label dimensions
        page_width = config.get('page_width_inch', 8.5) * inch
        page_height = config.get('page_height_inch', 11) * inch
        label_width = config.get('label_width', 1) * inch
        label_height = config.get('label_height', 1) * inch
        labels_per_row = config.get('labels_per_row', 3)
        labels_per_column = config.get('labels_per_column', 10)

        margin_top = config.get('margin_top', 0.5) * inch
        margin_bottom = config.get('margin_bottom', 0.5) * inch
        margin_left = config.get('margin_left', 0.1875) * inch
        margin_right = config.get('margin_right', 0.1875) * inch

        # Create a temporary directory for QR codes
        qr_dir = frappe.get_site_path('public', 'files', 'label_creator', 'qr_codes')
        os.makedirs(qr_dir, exist_ok=True)

        # Create canvas in memory with full page size
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

        # Calculate spacing
        usable_width = page_width - margin_left - margin_right
        usable_height = page_height - margin_top - margin_bottom

        # Draw all labels on the page
        for row in range(labels_per_column):
            for col in range(labels_per_row):
                x = margin_left + (col * label_width)
                y = page_height - margin_top - ((row + 1) * label_height)

                # Draw the label
                draw_label(
                    c,
                    x,
                    y,
                    sample_data['sku'],
                    sample_data['product'],
                    sample_data['display_price'],
                    label_width,
                    label_height,
                    config,
                    qr_dir
                )

        c.save()

        # Get the PDF data
        pdf_data = buffer.getvalue()
        buffer.close()

        # Convert PDF to image if PyMuPDF is available
        if has_pymupdf:
            # Open PDF from bytes
            pdf_document = fitz.open(stream=pdf_data, filetype="pdf")
            page = pdf_document[0]  # Get first page

            # Render page to image (zoom factor 2 for better quality)
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)

            # Convert to PNG
            img_data = pix.tobytes("png")
            pdf_document.close()

            # Convert to base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')

            return {
                "success": True,
                "image_data": img_base64,
                "image_type": "png",
                "message": "Preview generated successfully"
            }
        else:
            # Fallback to PDF if conversion library not available
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
            return {
                "success": True,
                "pdf_data": pdf_base64,
                "image_type": "pdf",
                "message": "Preview generated (install PyMuPDF for image preview)"
            }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Label Preview Error")
        return {
            "success": False,
            "message": str(e)
        }
