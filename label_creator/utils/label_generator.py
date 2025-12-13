import os
import json
import qrcode
import frappe
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph


def get_label_dimensions():
    """Load label dimensions from JSON file"""
    try:
        # Get the app path
        app_path = frappe.get_app_path('label_creator')
        json_path = os.path.join(app_path, 'data', 'labels_types.json')

        with open(json_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Load Label Dimensions Error")
        raise


def create_labels_pdf(labels_data, label_type):
    """
    Generate a PDF with labels based on the specified label type and product data
    """
    try:
        LABEL_DIMENSIONS = get_label_dimensions()

        if label_type not in LABEL_DIMENSIONS:
            raise ValueError(f"Unsupported label type: {label_type}")

        config = LABEL_DIMENSIONS[label_type]
        label_width = config["label_width"]
        label_height = config["label_height"]
        labels_per_row = config["labels_per_row"]
        labels_per_column = config["labels_per_column"]
        margin_top = config["margin_top"] * 72
        margin_bottom = config["margin_bottom"] * 72
        margin_left = config["margin_left"] * 72
        margin_right = config["margin_right"] * 72
        file_name = config["file_name"]

        page_width_pts = config["page_width_inch"] * 72
        page_height_pts = config["page_height_inch"] * 72

        usable_width = page_width_pts - margin_left - margin_right
        usable_height = page_height_pts - margin_top - margin_bottom

        horizontal_spacing = (
            (usable_width - (labels_per_row * label_width * 72)) / (labels_per_row - 1)
            if labels_per_row > 1 else 0
        )
        vertical_spacing = (
            (usable_height - (labels_per_column * label_height * 72)) / (labels_per_column - 1)
            if labels_per_column > 1 else 0
        )

        # Get current date
        current_date = datetime.now().strftime('%Y%m%d')

        # Create output directory in site's public folder
        site_path = frappe.utils.get_site_path()
        output_dir = os.path.join(site_path, 'public', 'files', 'label_creator')
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, f"{current_date}_{file_name}.pdf")

        # QR codes directory
        qr_dir = os.path.join(site_path, 'public', 'files', 'label_creator', 'qr_codes')
        os.makedirs(qr_dir, exist_ok=True)

        # Create canvas
        c = canvas.Canvas(output_path, pagesize=(page_width_pts, page_height_pts))

        x_start = margin_left
        y_start = page_height_pts - margin_top
        x_offset = x_start
        y_offset = y_start
        label_count = 0

        for item in labels_data:
            sku = item["sku"]
            product = item["product"]
            price = item["display_price"]
            quantity = item["quantity"]

            for _ in range(quantity):
                if label_count > 0 and label_count % (labels_per_row * labels_per_column) == 0:
                    c.showPage()
                    x_offset = x_start
                    y_offset = y_start

                draw_label(c, x_offset, y_offset, sku, product, price,
                          label_width, label_height, config, qr_dir)

                x_offset += label_width * 72 + horizontal_spacing
                if (label_count + 1) % labels_per_row == 0:
                    x_offset = x_start
                    y_offset -= label_height * 72 + vertical_spacing

                label_count += 1

        c.save()
        return output_path

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Labels PDF Error")
        raise


def draw_label(c, x, y, sku, name, price, label_width, label_height, config, qr_dir):
    """Draw a single label on the canvas"""
    label_width_pts = label_width * 72
    label_height_pts = label_height * 72
    qr_size_pts = min(label_width_pts, label_height_pts * 0.4)
    padding_pts = 4

    qr_x_offset = config.get("qrcode_x_offset", 0) * 72
    qr_y_offset = -1 * config.get("qrcode_y_offset", 0) * 72
    sku_x_offset = config.get("sku_x_offset", 0) * 72
    sku_y_offset = -1 * config.get("sku_y_offset", 0) * 72
    price_x_offset = config.get("price_x_offset", 0) * 72
    price_y_offset = -1 * config.get("price_y_offset", 0) * 72
    show_product_name = config.get("show_product_name", False)

    qr_path = os.path.join(qr_dir, f"{sku}.png")

    # Generate QR code if needed
    if not os.path.exists(qr_path):
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(sku)
        qr.make(fit=True)
        qr_img = qr.make_image(fill="black", back_color="white")
        qr_img.save(qr_path)

    # Draw QR code
    c.drawImage(
        qr_path,
        x + (label_width_pts - qr_size_pts) / 2 + qr_x_offset,
        y - qr_size_pts - padding_pts + qr_y_offset,
        width=qr_size_pts,
        height=qr_size_pts,
    )

    # Draw SKU
    sku_text_y = y - qr_size_pts - (5 * padding_pts)
    max_font_size = 8
    min_font_size = 5
    styles = getSampleStyleSheet()
    text_style = styles["BodyText"]
    text_style.alignment = 1

    font_size = max_font_size
    while font_size >= min_font_size:
        text_style.fontSize = font_size
        text_style.leading = font_size + 2
        sku_paragraph = Paragraph(sku, text_style)
        sku_width = label_width_pts - (2 * padding_pts)
        width, height = sku_paragraph.wrap(sku_width, qr_size_pts * 0.3)
        if height <= qr_size_pts * 0.3:
            break
        font_size -= 1

    sku_paragraph.drawOn(c, x + padding_pts, sku_text_y + sku_y_offset)

    if show_product_name:
        product_name_paragraph = Paragraph(name, text_style)
        product_name_width = label_width_pts - (2 * padding_pts)
        product_name_paragraph.wrap(product_name_width, label_height_pts * 0.2)
        product_name_paragraph.drawOn(c, x + padding_pts, sku_text_y - (2 * padding_pts))

    # Draw price
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(
        x + label_width_pts / 2 + price_x_offset,
        y - label_height_pts + (2 * padding_pts) + price_y_offset,
        f"${float(price):.2f}"
    )
