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
                "show_qr_code": lt.get("show_qr_code", 1),
                "qrcode_x_offset": lt.qrcode_x_offset or 0,
                "qrcode_y_offset": lt.qrcode_y_offset or 0,
                "qrcode_size_pts": lt.qrcode_size_pts or None,
                "show_sku": lt.get("show_sku", 1),
                "sku_x_offset": lt.sku_x_offset or 0,
                "sku_y_offset": lt.sku_y_offset or 0,
                "sku_font_type": lt.get("sku_font_type") or "Helvetica",
                "sku_font_size": lt.get("sku_font_size") or 7,
                "show_product_name": lt.get("show_product_name", 0),
                "product_name_x_offset": lt.get("product_name_x_offset") or 0,
                "product_name_y_offset": lt.get("product_name_y_offset") or 0,
                "product_name_font_type": lt.get("product_name_font_type") or "Helvetica",
                "product_name_font_size": lt.get("product_name_font_size") or 6,
                "show_price": lt.get("show_price", 1),
                "price_x_offset": lt.price_x_offset or 0,
                "price_y_offset": lt.price_y_offset or 0,
                "price_rotation": lt.price_rotation or 0,
                "price_font_type": lt.get("price_font_type") or "Helvetica-Bold",
                "price_font_size": lt.get("price_font_size") or 10,
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


def wrap_text(c, text, font_name, font_size, max_width_pts):
    """
    Wrap text to fit within max_width_pts.
    Returns a list of text lines.
    """
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        test_width = c.stringWidth(test_line, font_name, font_size)

        if test_width <= max_width_pts:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Single word is too long, add it anyway
                lines.append(word)

    if current_line:
        lines.append(current_line)

    return lines if lines else [text]


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

    # Offsets are specified as positive values:
    # - X offset: distance from LEFT edge of label (positive = move right)
    # - Y offset: distance from TOP edge of label (positive = move down)
    # Convert from inches to points here
    qr_x_offset = config.get("qrcode_x_offset", 0) * 72
    qr_y_offset = config.get("qrcode_y_offset", 0) * 72
    sku_x_offset = config.get("sku_x_offset", 0) * 72
    sku_y_offset = config.get("sku_y_offset", 0) * 72
    product_name_x_offset = config.get("product_name_x_offset", 0) * 72
    product_name_y_offset = config.get("product_name_y_offset", 0) * 72
    price_x_offset = config.get("price_x_offset", 0) * 72
    price_y_offset = config.get("price_y_offset", 0) * 72

    # Font settings
    sku_font_type = config.get("sku_font_type", "Helvetica")
    sku_font_size = config.get("sku_font_size", 7)
    product_name_font_type = config.get("product_name_font_type", "Helvetica")
    product_name_font_size = config.get("product_name_font_size", 6)
    price_font_type = config.get("price_font_type", "Helvetica-Bold")
    price_font_size = config.get("price_font_size", 10)

    # Retrieve (or generate) the QR code image
    qr_path = get_or_create_qr(sku, qr_dir)

    if orientation == "landscape":
        # Landscape Layout
        # Offsets are from: X = left edge, Y = top edge (positive Y goes down)

        # Draw the QR code if enabled
        if config.get("show_qr_code", True):
            qr_size_pts = label_height_pts * 0.8  # 80% of label height

            # Position from left edge + offset, and from top edge - offset
            # (subtract qr_size_pts because drawImage uses bottom-left corner)
            qr_x = x + qr_x_offset
            qr_y = y - qr_y_offset - qr_size_pts

            c.drawImage(
                qr_path,
                qr_x,
                qr_y,
                width=qr_size_pts,
                height=qr_size_pts,
                preserveAspectRatio=True,
                mask='auto'
            )

        # Draw the SKU text with wrapping if enabled
        if config.get("show_sku", True):
            # Calculate available width (label width minus x offset and some margin)
            available_width = label_width_pts - sku_x_offset - 5  # 5pt margin
            sku_lines = wrap_text(c, sku, sku_font_type, sku_font_size, available_width)

            sku_text_x = x + sku_x_offset
            sku_text_y = y - sku_y_offset - sku_font_size
            c.setFont(sku_font_type, sku_font_size)

            for i, line in enumerate(sku_lines):
                line_y = sku_text_y - (i * sku_font_size * 1.2)  # 1.2 = line spacing
                c.drawString(sku_text_x, line_y, line)

        # Draw product name if enabled with wrapping
        if config.get("show_product_name", False):
            available_width = label_width_pts - product_name_x_offset - 5
            product_lines = wrap_text(c, name, product_name_font_type, product_name_font_size, available_width)

            product_text_x = x + product_name_x_offset
            product_text_y = y - product_name_y_offset - product_name_font_size
            c.setFont(product_name_font_type, product_name_font_size)

            for i, line in enumerate(product_lines):
                line_y = product_text_y - (i * product_name_font_size * 1.2)
                c.drawString(product_text_x, line_y, line)

        # Draw the price if enabled
        if config.get("show_price", True):
            price_text = f"${float(price):.2f}"
            price_x = x + price_x_offset
            price_y = y - price_y_offset
            price_rotation = config.get("price_rotation", 90)
            draw_rotated_text(c, price_text, price_x, price_y, angle=price_rotation,
                              font_name=price_font_type, font_size=price_font_size)

    else:
        # Portrait Layout
        # Pure offset positioning: X from left edge, Y from top edge
        # When offsets are 0, elements appear at top-left corner

        # Draw QR code if enabled
        if config.get("show_qr_code", True):
            qr_size_pts = min(label_width_pts, label_height_pts * 0.4)

            # Position purely from offsets (no automatic centering)
            qr_x = x + qr_x_offset
            qr_y = y - qr_y_offset - qr_size_pts
            c.drawImage(
                qr_path,
                qr_x,
                qr_y,
                width=qr_size_pts,
                height=qr_size_pts,
                preserveAspectRatio=True,
                mask='auto'
            )

        # Draw SKU text with wrapping if enabled
        if config.get("show_sku", True):
            # Calculate available width (label width minus x offset and some margin)
            available_width = label_width_pts - sku_x_offset - 5  # 5pt margin
            sku_lines = wrap_text(c, sku, sku_font_type, sku_font_size, available_width)

            sku_text_x = x + sku_x_offset
            sku_text_y = y - sku_y_offset - sku_font_size
            c.setFont(sku_font_type, sku_font_size)

            for i, line in enumerate(sku_lines):
                line_y = sku_text_y - (i * sku_font_size * 1.2)  # 1.2 = line spacing
                c.drawString(sku_text_x, line_y, line)

        # Draw product name if enabled with wrapping
        if config.get("show_product_name", False):
            available_width = label_width_pts - product_name_x_offset - 5
            product_lines = wrap_text(c, name, product_name_font_type, product_name_font_size, available_width)

            product_text_x = x + product_name_x_offset
            product_text_y = y - product_name_y_offset - product_name_font_size
            c.setFont(product_name_font_type, product_name_font_size)

            for i, line in enumerate(product_lines):
                line_y = product_text_y - (i * product_name_font_size * 1.2)
                c.drawString(product_text_x, line_y, line)

        # Draw price if enabled
        if config.get("show_price", True):
            price_text_x = x + price_x_offset
            price_text_y = y - price_y_offset - price_font_size
            c.setFont(price_font_type, price_font_size)
            c.drawString(price_text_x, price_text_y, f"${float(price):.2f}")


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
