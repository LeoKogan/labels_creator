import os
import json
import qrcode
import frappe
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph


def get_currency_info(currency_code):
    """
    Get currency information from ERPNext Currency doctype
    Returns dict with symbol, symbol_on_right, and number_format
    """
    try:
        if currency_code and frappe.db.exists("Currency", currency_code):
            currency = frappe.get_doc("Currency", currency_code)
            return {
                'symbol': currency.symbol or '$',
                'symbol_on_right': currency.symbol_on_right or 0,
                'number_format': currency.number_format or '#,##0.00'
            }
    except Exception as e:
        frappe.log_error(f"Error fetching currency {currency_code}: {str(e)}", "Currency Fetch Error")

    # Default to USD format
    return {
        'symbol': '$',
        'symbol_on_right': 0,
        'number_format': '#,##0.00'
    }


def format_price(price, currency_info):
    """
    Format price with currency symbol based on currency settings
    """
    symbol = currency_info.get('symbol', '$')
    symbol_on_right = currency_info.get('symbol_on_right', 0)

    # Format the price as a float with 2 decimal places
    formatted_price = f"{float(price):.2f}"

    # Place symbol based on symbol_on_right setting
    if symbol_on_right:
        return f"{formatted_price}{symbol}"
    else:
        return f"{symbol}{formatted_price}"


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
                "sku_sample": lt.get("sku_sample") or "SAM-PLE-SKU",
                "sku_x_offset": lt.sku_x_offset or 0,
                "sku_y_offset": lt.sku_y_offset or 0,
                "sku_font_type": lt.get("sku_font_type") or "Helvetica",
                "sku_font_size": lt.get("sku_font_size") or 7,
                "sku_max_word_length": lt.get("sku_max_word_length") or 9,
                "sku_text_align": lt.get("sku_text_align") or "Left",
                "show_product_name": lt.get("show_product_name", 0),
                "product_name_sample": lt.get("product_name_sample") or "Sample Product Name",
                "product_name_x_offset": lt.get("product_name_x_offset") or 0,
                "product_name_y_offset": lt.get("product_name_y_offset") or 0,
                "product_name_font_type": lt.get("product_name_font_type") or "Helvetica",
                "product_name_font_size": lt.get("product_name_font_size") or 6,
                "product_name_max_word_length": lt.get("product_name_max_word_length") or 9,
                "product_name_text_align": lt.get("product_name_text_align") or "Left",
                "show_price": lt.get("show_price", 1),
                "price_sample": lt.get("price_sample") or 29.99,
                "currency": lt.get("currency") or "USD",
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


def wrap_text(c, text, font_name, font_size, max_width_pts, max_word_length=None):
    """
    Wrap text to fit within max_width_pts.
    Returns a list of text lines.

    Priority order:
    1. Try to fit whole words within max_width_pts (don't break on hyphens or spaces yet)
    2. If word doesn't fit, break on hyphens
    3. If max_word_length is set and any part exceeds it, split at character boundaries

    This ensures Max Word Length takes precedence before breaking on hyphens or spaces.
    """
    import re

    # Split on spaces first
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        # PRIORITY 1: Try to fit the whole word first (including hyphens)
        test_line = current_line + (" " if current_line else "") + word
        test_width = c.stringWidth(test_line, font_name, font_size)

        if test_width <= max_width_pts:
            # Word fits, add it
            current_line = test_line
        else:
            # Word doesn't fit within available width
            if current_line:
                lines.append(current_line)
                current_line = ""

            # PRIORITY 2: Check if word has hyphens - break on hyphens if needed
            if '-' in word:
                # Split on hyphens: "ABC-DEF-GHI" -> ["ABC-", "DEF-", "GHI"]
                parts = word.split('-')
                hyphen_parts = [p + '-' for p in parts[:-1]] + [parts[-1]]

                # PRIORITY 3: If max_word_length is set, check each part and split if needed
                if max_word_length:
                    final_parts = []
                    for part in hyphen_parts:
                        if len(part) > max_word_length:
                            # Split this part at character boundaries
                            for i in range(0, len(part), max_word_length):
                                final_parts.append(part[i:i+max_word_length])
                        else:
                            final_parts.append(part)
                    hyphen_parts = final_parts

                # Now try to fit parts on lines
                for part in hyphen_parts:
                    test_line = current_line + (" " if current_line else "") + part
                    test_width = c.stringWidth(test_line, font_name, font_size)

                    if test_width <= max_width_pts:
                        current_line = test_line
                    else:
                        if current_line:
                            lines.append(current_line)
                        current_line = part
            else:
                # No hyphens in word
                # PRIORITY 3: If max_word_length is set and word is too long, split at character boundaries
                if max_word_length and len(word) > max_word_length:
                    word_chunks = [word[i:i+max_word_length] for i in range(0, len(word), max_word_length)]

                    for chunk in word_chunks:
                        test_line = current_line + (" " if current_line else "") + chunk
                        test_width = c.stringWidth(test_line, font_name, font_size)

                        if test_width <= max_width_pts:
                            current_line = test_line
                        else:
                            if current_line:
                                lines.append(current_line)
                            current_line = chunk
                else:
                    # Word doesn't fit and no way to split it, add it anyway
                    current_line = word

    if current_line:
        lines.append(current_line)

    return lines if lines else [text]


def draw_aligned_text(c, text, x, y, font_name, font_size, alignment="Left", available_width=None):
    """
    Draw text with specified alignment.

    Args:
        c: ReportLab canvas
        text: Text to draw
        x: X position (for Left alignment, this is the left edge; for Centre/Right, this is relative to available_width)
        y: Y position
        font_name: Font name
        font_size: Font size
        alignment: "Left", "Centre", or "Right"
        available_width: Available width for Centre/Right alignment (in points)
    """
    text_width = c.stringWidth(text, font_name, font_size)

    if alignment == "Centre":
        # Center the text within available width
        if available_width:
            draw_x = x + (available_width - text_width) / 2
        else:
            draw_x = x - text_width / 2
    elif alignment == "Right":
        # Right align the text within available width
        if available_width:
            draw_x = x + available_width - text_width
        else:
            draw_x = x - text_width
    else:  # Left alignment (default)
        draw_x = x

    c.drawString(draw_x, y, text)


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
    sku_max_word_length = config.get("sku_max_word_length")
    sku_text_align = config.get("sku_text_align", "Left")
    product_name_font_type = config.get("product_name_font_type", "Helvetica")
    product_name_font_size = config.get("product_name_font_size", 6)
    product_name_max_word_length = config.get("product_name_max_word_length")
    product_name_text_align = config.get("product_name_text_align", "Left")
    price_font_type = config.get("price_font_type", "Helvetica-Bold")
    price_font_size = config.get("price_font_size", 10)

    # Get currency information from ERPNext Currency doctype
    currency_code = config.get("currency", "USD")
    currency_info = get_currency_info(currency_code)

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
            # Calculate available width (label width minus x offset and right margin)
            available_width = label_width_pts - sku_x_offset - 10  # 10pt right margin
            sku_lines = wrap_text(c, sku, sku_font_type, sku_font_size, available_width, sku_max_word_length)

            sku_text_x = x + sku_x_offset
            sku_text_y = y - sku_y_offset - sku_font_size
            c.setFont(sku_font_type, sku_font_size)

            for i, line in enumerate(sku_lines):
                line_y = sku_text_y - (i * sku_font_size * 1.2)  # 1.2 = line spacing
                draw_aligned_text(c, line, sku_text_x, line_y, sku_font_type, sku_font_size, sku_text_align, available_width)

        # Draw product name if enabled with wrapping
        if config.get("show_product_name", False):
            available_width = label_width_pts - product_name_x_offset - 10  # 10pt right margin
            product_lines = wrap_text(c, name, product_name_font_type, product_name_font_size, available_width, product_name_max_word_length)

            product_text_x = x + product_name_x_offset
            product_text_y = y - product_name_y_offset - product_name_font_size
            c.setFont(product_name_font_type, product_name_font_size)

            for i, line in enumerate(product_lines):
                line_y = product_text_y - (i * product_name_font_size * 1.2)
                draw_aligned_text(c, line, product_text_x, line_y, product_name_font_type, product_name_font_size, product_name_text_align, available_width)

        # Draw the price if enabled
        if config.get("show_price", True):
            price_text = format_price(price, currency_info)
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
            # Calculate available width (label width minus x offset and right margin)
            available_width = label_width_pts - sku_x_offset - 10  # 10pt right margin
            sku_lines = wrap_text(c, sku, sku_font_type, sku_font_size, available_width, sku_max_word_length)

            sku_text_x = x + sku_x_offset
            sku_text_y = y - sku_y_offset - sku_font_size
            c.setFont(sku_font_type, sku_font_size)

            for i, line in enumerate(sku_lines):
                line_y = sku_text_y - (i * sku_font_size * 1.2)  # 1.2 = line spacing
                draw_aligned_text(c, line, sku_text_x, line_y, sku_font_type, sku_font_size, sku_text_align, available_width)

        # Draw product name if enabled with wrapping
        if config.get("show_product_name", False):
            available_width = label_width_pts - product_name_x_offset - 10  # 10pt right margin
            product_lines = wrap_text(c, name, product_name_font_type, product_name_font_size, available_width, product_name_max_word_length)

            product_text_x = x + product_name_x_offset
            product_text_y = y - product_name_y_offset - product_name_font_size
            c.setFont(product_name_font_type, product_name_font_size)

            for i, line in enumerate(product_lines):
                line_y = product_text_y - (i * product_name_font_size * 1.2)
                draw_aligned_text(c, line, product_text_x, line_y, product_name_font_type, product_name_font_size, product_name_text_align, available_width)

        # Draw price if enabled
        if config.get("show_price", True):
            price_text_x = x + price_x_offset
            price_text_y = y - price_y_offset - price_font_size
            c.setFont(price_font_type, price_font_size)
            c.drawString(price_text_x, price_text_y, format_price(price, currency_info))


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
