import os
import json
import qrcode
import frappe
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph


def get_label_dimensions():
    """Load label dimensions from Label Type DocType"""
    try:
        # Get all Label Type documents
        label_types_list = frappe.get_all(
            "Label Type",
            fields=["*"],
            order_by="label_type_name"
        )

        # Convert to dictionary format for compatibility
        data = {}
        for lt in label_types_list:
            data[lt.label_type_name] = {
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
        return data
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Load Label Dimensions Error")
        raise


def get_or_create_qr(sku, qr_dir):
    """
    Retrieve (or generate) the QR code image for a given SKU.
    """
    qr_path = os.path.join(qr_dir, f"{sku}.png")
    if not os.path.exists(qr_path):
        qr = qrcode.QRCode(box_size=10, border=1)
        qr.add_data(sku)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save(qr_path)
    return qr_path


def draw_rotated_text(c, text, center_x, center_y, angle, font_name="Helvetica-Bold", font_size=8):
    """
    Draw rotated text centered around (center_x, center_y).
    """
    c.saveState()
    c.translate(center_x, center_y)
    c.rotate(angle)
    c.setFont(font_name, font_size)
    text_width = c.stringWidth(text, font_name, font_size)
    c.drawString(-text_width/2, -font_size/2, text)
    c.restoreState()


def draw_label(c, x, y, sku, name, price, label_width, label_height, config, qr_dir):
    """
    Draw a single label on the ReportLab canvas.

    For landscape orientation:
      - The QR code is drawn on the left.
      - The SKU (and optionally the product name) is drawn to the right of the QR.
      - The price is drawn at the far right edge and rotated by the angle specified in config.

    For portrait orientation:
      - The QR code is centered at the top.
      - The SKU (and optionally the product name) is drawn below the QR.
      - The price is drawn near the bottom.
    """
    orientation = config.get("label_orientation", "portrait").lower()

    # Convert label dimensions from inches to points (1 inch = 72 points)
    label_width_pts = label_width * 72
    label_height_pts = label_height * 72

    # Offsets (provided in inches; conversion to points is done here)
    qr_x_offset = config.get("qrcode_x_offset", 0) * 72
    qr_y_offset = -config.get("qrcode_y_offset", 0) * 72
    sku_x_offset = config.get("sku_x_offset", 0) * 72
    sku_y_offset = -config.get("sku_y_offset", 0) * 72
    product_name_x_offset = config.get("product_name_x_offset", 0) * 72
    product_name_y_offset = -config.get("product_name_y_offset", 0) * 72
    price_x_offset = config.get("price_x_offset", 0) * 72
    price_y_offset = -config.get("price_y_offset", 0) * 72

    # Retrieve (or generate) the QR code image
    qr_path = get_or_create_qr(sku, qr_dir)

    if orientation == "landscape":
        # Landscape Layout
        # Layout: QR on left | SKU and Product Name stacked on right | Price rotated at far right

        qr_size_pts = label_height_pts * 0.8  # 80% of label height

        # Draw the QR code on the left
        qr_x = x + qr_x_offset
        qr_y = y + qr_y_offset - qr_size_pts

        c.drawImage(
            qr_path,
            qr_x,
            qr_y,
            width=qr_size_pts,
            height=qr_size_pts,
            preserveAspectRatio=True,
            mask='auto'
        )

        # Calculate text area to the right of QR
        text_area_x = x + qr_size_pts + 3 + sku_x_offset  # 3pts spacing after QR
        text_area_width = label_width_pts - qr_size_pts - 10  # Reserve space for price

        # Draw the SKU text to the right of QR, at the top
        sku_text_x = text_area_x
        sku_text_y = qr_y + qr_size_pts - 10 + sku_y_offset  # Start near top
        styles = getSampleStyleSheet()
        text_style = styles["BodyText"]
        text_style.fontSize = 7
        text_style.leading = 8
        text_style.alignment = 0  # left alignment
        sku_paragraph = Paragraph(sku, text_style)
        sku_paragraph.wrap(text_area_width, 12)  # Max height for SKU
        sku_paragraph.drawOn(c, sku_text_x, sku_text_y)

        # Draw product name below SKU if enabled
        if config.get("show_product_name", False):
            product_text_x = text_area_x + product_name_x_offset
            product_text_y = sku_text_y - 15 + product_name_y_offset  # 15pts below SKU

            product_style = styles["BodyText"]
            product_style.fontSize = 6
            product_style.leading = 7
            product_style.alignment = 0  # left alignment
            product_paragraph = Paragraph(name, product_style)
            product_paragraph.wrap(text_area_width, qr_size_pts * 0.4)  # Max height for product
            product_paragraph.drawOn(c, product_text_x, product_text_y)

        # Draw the price at the far right edge, rotated
        price_text = f"${float(price):.2f}"
        price_x = x + label_width_pts + price_x_offset
        price_y = qr_y + (qr_size_pts / 2) + price_y_offset  # Centered vertically
        price_rotation = config.get("price_rotation", 90)
        draw_rotated_text(c, price_text, price_x, price_y, angle=price_rotation,
                          font_name="Helvetica-Bold", font_size=7)

    else:
        # Portrait Layout
        # Layout from top to bottom: QR code → SKU → Product Name (optional) → Price

        qr_size_pts = min(label_width_pts, label_height_pts * 0.4)

        # Draw QR code at the top
        qr_y = y - qr_size_pts + qr_y_offset
        c.drawImage(
            qr_path,
            x + (label_width_pts - qr_size_pts) / 2 + qr_x_offset,
            qr_y,
            width=qr_size_pts,
            height=qr_size_pts,
            preserveAspectRatio=True,
            mask='auto'
        )

        # Draw SKU text below QR code
        sku_text_x = x + sku_x_offset
        sku_text_y = qr_y - 12 + sku_y_offset  # 12pts below QR for spacing
        styles = getSampleStyleSheet()
        text_style = styles["BodyText"]
        text_style.fontSize = 7
        text_style.leading = 8
        text_style.alignment = 1  # Center alignment
        sku_paragraph = Paragraph(sku, text_style)
        sku_width = label_width_pts
        sku_paragraph.wrap(sku_width, 15)  # Max height for SKU
        sku_paragraph.drawOn(c, sku_text_x, sku_text_y)

        # Draw product name below SKU if enabled
        if config.get("show_product_name", False):
            product_text_style = styles["BodyText"]
            product_text_style.fontSize = 6
            product_text_style.leading = 7
            product_text_style.alignment = 1  # Center alignment
            product_name_paragraph = Paragraph(name, product_text_style)
            product_name_width = label_width_pts
            product_name_paragraph.wrap(product_name_width, 20)  # Max height for product name
            product_name_x = x + product_name_x_offset
            product_name_y = sku_text_y - 18 + product_name_y_offset  # 18pts below SKU
            product_name_paragraph.drawOn(c, product_name_x, product_name_y)

        # Draw price at the bottom
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(
            x + label_width_pts / 2 + price_x_offset,
            y - label_height_pts + 5 + price_y_offset,  # 5pts from bottom
            f"${float(price):.2f}"
        )


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
