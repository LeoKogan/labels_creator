"""
Native (reportlab) PDF renderer for the Gift Certificate print, following
the same approach as utils/label_generator.py for product labels: draw
everything ourselves so the output is pixel-exact and independent of
Frappe's wkhtmltopdf print pipeline, which (a) has weak/inconsistent
flexbox support - producing a visibly different, broken layout compared
to the browser preview of the old Jinja Print Format - and (b) forces the
PDF page size from Print Settings (defaulting to A4) regardless of any
`@page` CSS rule, ignoring the Gift Certificate Type's configured size.
"""

import hashlib
import os
from io import BytesIO

import frappe
import qrcode
from reportlab.lib.colors import HexColor, white
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from label_creator.utils.label_generator import draw_aligned_text, wrap_text

try:
	import barcode
	from barcode.writer import ImageWriter
	HAS_BARCODE = True
except ImportError:
	HAS_BARCODE = False

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"

PAD_TOP = 9 * mm
PAD_SIDE = 8 * mm
PAD_BOTTOM = 7 * mm
FRAME_MARGIN = 3 * mm


def get_gift_certificate_type(doc):
	return frappe.get_doc("Gift Certificate Type", doc.gift_certificate_type or "Standard")


def get_assets_dir():
	site_path = frappe.utils.get_site_path()
	assets_dir = os.path.join(site_path, "public", "files", "label_creator", "gift_certificates")
	os.makedirs(assets_dir, exist_ok=True)
	return assets_dir


def generate_gift_certificate_pdf(doc, gc_type=None):
	"""Render a single Gift Certificate to a one-page PDF. Returns PDF bytes."""
	gc_type = gc_type or get_gift_certificate_type(doc)
	assets_dir = get_assets_dir()

	buffer = BytesIO()
	c = canvas.Canvas(buffer)
	_draw_certificate_page(c, doc, gc_type, assets_dir)
	c.save()
	return buffer.getvalue()


def generate_bulk_gift_certificate_pdf(names):
	"""
	Render multiple Gift Certificates into a single combined PDF, one page
	per certificate, each page sized to that certificate's own Gift
	Certificate Type - reportlab supports a different page size per page
	within one document, so no separate PDF-merge step is needed the way
	Frappe's own multi-doc print does it.
	"""
	assets_dir = get_assets_dir()
	buffer = BytesIO()
	c = canvas.Canvas(buffer)

	for name in names:
		doc = frappe.get_doc("Gift Certificate", name)
		gc_type = get_gift_certificate_type(doc)
		_draw_certificate_page(c, doc, gc_type, assets_dir)

	c.save()
	return buffer.getvalue()


def _draw_certificate_page(c, doc, gc_type, assets_dir):
	width_pt = gc_type.card_width_mm * mm
	height_pt = gc_type.card_height_mm * mm
	c.setPageSize((width_pt, height_pt))

	bg_color = _safe_color(gc_type.background_color, "#0b574d")
	accent_start = _safe_color(gc_type.accent_color_start, "#2dd4bf")
	accent_end = _safe_color(gc_type.accent_color_end, "#0d9488")

	# Background
	c.setFillColor(bg_color)
	c.rect(0, 0, width_pt, height_pt, fill=1, stroke=0)

	if gc_type.show_dot_pattern:
		_draw_dot_pattern(c, width_pt, height_pt)

	# Framed edge (two-tone inset ring)
	c.setStrokeColor(white)
	c.setLineWidth(1)
	c.roundRect(FRAME_MARGIN, FRAME_MARGIN, width_pt - 2 * FRAME_MARGIN, height_pt - 2 * FRAME_MARGIN, 3, stroke=1, fill=0)
	c.setStrokeColor(accent_end)
	c.setLineWidth(2)
	inset = FRAME_MARGIN + 1.6 * mm
	c.roundRect(inset, inset, width_pt - 2 * inset, height_pt - 2 * inset, 3, stroke=1, fill=0)

	content_width = width_pt - 2 * PAD_SIDE
	redeem_url = (gc_type.qr_redeem_base_url or "") + (doc.certificate_code or "")
	qr_path = _get_or_create_qr(redeem_url, assets_dir, "redeem") if gc_type.show_qr_code else None
	barcode_path = _get_or_create_barcode(
		doc.certificate_code, assets_dir, gc_type.barcode_type or "code128"
	) if gc_type.show_barcode else None
	social_qr_path = _get_or_create_qr(
		gc_type.social_url, assets_dir, "social"
	) if gc_type.show_footer_links and gc_type.social_url else None

	recipient_name = _recipient_name(doc, gc_type)
	recipient_lines = wrap_text(c, recipient_name, FONT_BOLD, 16, content_width)
	conditions_lines = (
		wrap_text(c, gc_type.conditions_text, FONT_BOLD, 7.3, content_width)
		if gc_type.conditions_text else []
	)

	# Build the top-down "flow" sections (mirrors the old CSS flex column
	# with justify-content:space-between): anything positioned "Custom" is
	# drawn separately, out of this stack, same as position:absolute did.
	sections = []
	sections.append(("header", _header_height(gc_type)))
	sections.append(("recipient", _recipient_height(gc_type, recipient_lines)))
	sections.append(("value", _value_height()))
	if gc_type.show_qr_code and gc_type.qr_position != "Custom Position":
		sections.append(("qr", _qr_height(gc_type)))
	sections.append(("details", _details_height()))
	sections.append(("footer", _footer_height(gc_type, barcode_path, conditions_lines)))

	content_height = height_pt - PAD_TOP - PAD_BOTTOM
	natural_height = sum(h for _, h in sections)
	gap_count = max(len(sections) - 1, 0)
	leftover = content_height - natural_height
	# Mirrors CSS justify-content:space-between - gaps expand to fill extra
	# room on a spacious page (A4/A5) and shrink toward 0 on a tight one
	# (A6). Never force a minimum gap: on a card where content barely fits,
	# that would push it past the bottom edge instead of just packing tight.
	gap = max(leftover / gap_count, 0) if gap_count else 0

	y = height_pt - PAD_TOP
	for name, h in sections:
		if name == "header":
			_draw_header(c, gc_type, width_pt, y)
		elif name == "recipient":
			_draw_recipient(c, gc_type, width_pt, y, recipient_lines)
		elif name == "value":
			_draw_value(c, doc, gc_type, width_pt, y)
		elif name == "qr":
			_draw_qr(c, gc_type, width_pt, y, qr_path)
		elif name == "details":
			_draw_details(c, doc, gc_type, width_pt, y, content_width)
		elif name == "footer":
			_draw_footer(c, doc, gc_type, width_pt, y, barcode_path, social_qr_path, conditions_lines)
		y -= h + gap

	# Custom-positioned QR/barcode are anchored independently of the flow.
	if gc_type.show_qr_code and gc_type.qr_position == "Custom Position" and qr_path:
		size = gc_type.qr_size_mm * mm
		cx = width_pt * (gc_type.qr_x_offset_pct or 50) / 100
		cy = height_pt * (1 - (gc_type.qr_y_offset_pct or 50) / 100)
		_draw_image_card(c, qr_path, cx - size / 2, cy - size / 2, size, size)

	if gc_type.show_barcode and gc_type.barcode_position == "Custom Position" and barcode_path:
		bh = gc_type.barcode_height_mm * mm
		bw = bh * 3
		cx = width_pt * (gc_type.barcode_x_offset_pct or 50) / 100
		cy = height_pt * (1 - (gc_type.barcode_y_offset_pct or 90) / 100)
		_draw_image_card(c, barcode_path, cx - bw / 2, cy - bh / 2, bw, bh)

	c.showPage()


# --- section height estimators (points) -------------------------------

def _header_height(gc_type):
	h = 34 if not gc_type.logo_url else 30  # badge circle or logo box
	h += 4 + 20  # gap + title line
	if gc_type.tagline_text:
		h += 3 + 11
	h += 8 + 5  # divider gap + divider itself
	return h


def _recipient_height(gc_type, recipient_lines):
	return 11 + 3 + len(recipient_lines) * 18


def _value_height():
	return 11 + 4 + 34  # label + gap + amount box


def _qr_height(gc_type):
	return gc_type.qr_size_mm * mm + 5 + 11


def _details_height():
	return 34


def _footer_height(gc_type, barcode_path, conditions_lines):
	h = 0
	if barcode_path and gc_type.barcode_position != "Custom Position":
		# Must match _draw_footer's box_h (bh + 4mm) plus its 5pt gap-after
		h += gc_type.barcode_height_mm * mm + 4 * mm + 5
	if conditions_lines:
		h += len(conditions_lines) * 8 + 5
	if gc_type.show_footer_links:
		h += _footer_links_height(gc_type)
	return h


def _footer_links_height(gc_type):
	"""Tallest item in the footer links row - a plain text link is ~12pt,
	but the social-follow QR block can be much taller than that."""
	height = 12
	if gc_type.social_url:
		height = max(height, (gc_type.social_qr_size_mm or 10) * mm)
	return height


# --- section drawers ----------------------------------------------------

def _draw_header(c, gc_type, width_pt, top_y):
	cx = width_pt / 2

	if gc_type.logo_url:
		logo_path = _resolve_logo(gc_type.logo_url, get_assets_dir())
	else:
		logo_path = None

	if logo_path:
		try:
			from reportlab.lib.utils import ImageReader
			img = ImageReader(logo_path)
			iw, ih = img.getSize()
			target_h = 12 * mm
			target_w = target_h * iw / ih
			box_w, box_h = target_w + 8 * mm, target_h + 3 * mm
			_draw_rounded_card(c, cx - box_w / 2, top_y - box_h, box_w, box_h, 3, white)
			c.drawImage(img, cx - target_w / 2, top_y - box_h + (box_h - target_h) / 2,
				width=target_w, height=target_h, preserveAspectRatio=True, mask="auto")
			y = top_y - box_h - 4
		except Exception:
			logo_path = None

	if not logo_path:
		r = 15
		ccy = top_y - r
		c.setFillColorRGB(1, 1, 1, alpha=0.14)
		c.circle(cx, ccy, r, fill=1, stroke=0)
		c.setStrokeColorRGB(1, 1, 1, alpha=0.55)
		c.setLineWidth(1.2)
		c.circle(cx, ccy, r, fill=0, stroke=1)
		_draw_gift_icon(c, cx, ccy, 8, white)
		y = top_y - 2 * r - 4

	c.setFillColor(white)
	c.setFont(FONT_BOLD, 18)
	c.drawCentredString(cx, y - 14, gc_type.title_text or "")
	y -= 20

	if gc_type.tagline_text:
		c.setFillColorRGB(1, 1, 1, alpha=0.88)
		c.setFont(FONT_ITALIC, 9.5)
		c.drawCentredString(cx, y - 8, gc_type.tagline_text)
		y -= 3 + 11

	y -= 8
	accent_start = _safe_color(gc_type.accent_color_start, "#2dd4bf")
	c.setStrokeColor(accent_start)
	c.setLineWidth(1.6)
	c.line(cx - 15, y, cx - 4, y)
	c.line(cx + 4, y, cx + 15, y)
	c.setFillColor(accent_start)
	c.circle(cx, y, 1.6, fill=1, stroke=0)


def _draw_recipient(c, gc_type, width_pt, top_y, recipient_lines):
	cx = width_pt / 2
	c.setFillColorRGB(1, 1, 1, alpha=0.85)
	c.setFont(FONT_BOLD, 9)
	c.drawCentredString(cx, top_y - 9, (gc_type.recipient_label or "").upper())

	y = top_y - 9 - 3 - 14
	max_line_width = 0
	for line in recipient_lines:
		max_line_width = max(max_line_width, c.stringWidth(line, FONT_BOLD, 16))
		c.setFillColor(white)
		c.setFont(FONT_BOLD, 16)
		c.drawCentredString(cx, y, line)
		y -= 18

	underline_y = y + 18 - 5
	c.setStrokeColorRGB(1, 1, 1, alpha=0.4)
	c.setLineWidth(1.1)
	c.line(cx - max_line_width / 2 - 2, underline_y, cx + max_line_width / 2 + 2, underline_y)


def _draw_value(c, doc, gc_type, width_pt, top_y):
	cx = width_pt / 2
	c.setFillColorRGB(1, 1, 1, alpha=0.85)
	c.setFont(FONT_BOLD, 9)
	c.drawCentredString(cx, top_y - 9, (gc_type.value_label or "").upper())

	box_y = top_y - 9 - 4 - 34
	_draw_rounded_card(c, PAD_SIDE, box_y, width_pt - 2 * PAD_SIDE, 34, 6, white)

	amount_text = frappe.utils.fmt_money(doc.amount, currency=gc_type.default_currency)
	c.setFillColor(HexColor("#0b2e2a"))
	c.setFont(FONT_BOLD, 22)
	c.drawCentredString(cx, box_y + 11, amount_text)


def _draw_qr(c, gc_type, width_pt, top_y, qr_path):
	cx = width_pt / 2
	size = gc_type.qr_size_mm * mm
	box_y = top_y - size
	if qr_path:
		_draw_image_card(c, qr_path, cx - size / 2, box_y, size, size)

	if gc_type.qr_instruction_text:
		c.setFillColorRGB(1, 1, 1, alpha=0.9)
		c.setFont(FONT_BOLD, 8.5)
		c.drawCentredString(cx, box_y - 11, gc_type.qr_instruction_text.upper())


def _draw_details(c, doc, gc_type, width_pt, top_y, content_width):
	box_h = 34
	box_y = top_y - box_h
	_draw_rounded_card(c, PAD_SIDE, box_y, content_width, box_h, 6, white)

	col_w = content_width / 2
	label_color = _safe_color(gc_type.background_color, "#0b574d")

	c.setFillColor(label_color)
	c.setFont(FONT_BOLD, 7.5)
	c.drawCentredString(PAD_SIDE + col_w / 2, box_y + box_h - 12, (gc_type.code_label or "").upper())
	c.setFillColor(HexColor("#000000"))
	c.setFont(FONT_BOLD, 9.5)
	c.drawCentredString(PAD_SIDE + col_w / 2, box_y + box_h - 24, doc.certificate_code or "")

	expiry_text = (
		frappe.utils.formatdate(doc.expiration, "MMM d, yyyy") if doc.expiration
		else (gc_type.no_expiration_text or "")
	)
	c.setFillColor(label_color)
	c.setFont(FONT_BOLD, 7.5)
	c.drawCentredString(PAD_SIDE + col_w + col_w / 2, box_y + box_h - 12, (gc_type.expiry_label or "").upper())
	c.setFillColor(HexColor("#000000"))
	c.setFont(FONT_BOLD, 9.5)
	c.drawCentredString(PAD_SIDE + col_w + col_w / 2, box_y + box_h - 24, expiry_text)

	c.setStrokeColor(HexColor("#e2e8f0"))
	c.setLineWidth(1)
	c.line(PAD_SIDE + col_w, box_y + 5, PAD_SIDE + col_w, box_y + box_h - 5)


def _draw_footer(c, doc, gc_type, width_pt, top_y, barcode_path, social_qr_path, conditions_lines):
	cx = width_pt / 2
	y = top_y

	if barcode_path and gc_type.barcode_position != "Custom Position":
		bh = gc_type.barcode_height_mm * mm
		bw = bh * 3
		box_h = bh + 4 * mm
		box_y = y - box_h
		_draw_rounded_card(c, cx - bw / 2 - 4 * mm, box_y, bw + 8 * mm, box_h, 4, white)
		c.drawImage(barcode_path, cx - bw / 2, box_y + box_h - bh - 2, width=bw, height=bh,
			preserveAspectRatio=True, mask="auto")
		c.setFillColor(HexColor("#000000"))
		c.setFont(FONT_BOLD, 7.5)
		c.drawCentredString(cx, box_y + 3, doc.certificate_code or "")
		y = box_y - 5

	for line in conditions_lines:
		c.setFillColorRGB(1, 1, 1, alpha=0.85)
		c.setFont(FONT_BOLD, 7.3)
		c.drawCentredString(cx, y - 6, line)
		y -= 8
	if conditions_lines:
		y -= 5

	if gc_type.show_footer_links:
		_draw_footer_links(c, gc_type, width_pt, y, social_qr_path)


def _draw_footer_links(c, gc_type, width_pt, top_y, social_qr_path):
	items_width = []
	website_text = gc_type.website_label or ""
	if gc_type.website_url:
		items_width.append(("website", 12 + c.stringWidth(website_text, FONT_BOLD, 10)))

	social_size = 0
	if gc_type.social_url and social_qr_path:
		social_size = (gc_type.social_qr_size_mm or 10) * mm
		follow_text = gc_type.social_follow_text or "Follow us!"
		handle_w = 12 + c.stringWidth(gc_type.social_label or "", FONT_BOLD, 9)
		text_block_w = max(c.stringWidth(follow_text.upper(), FONT_BOLD, 7.5), handle_w)
		items_width.append(("social", social_size + 6 + text_block_w))

	gap = 12
	total_w = sum(w for _, w in items_width) + gap * max(len(items_width) - 1, 0)
	x = width_pt / 2 - total_w / 2

	for kind, w in items_width:
		if kind == "website":
			c.setFillColor(white)
			c.setFont(FONT_BOLD, 10)
			c.drawString(x, top_y - 9, website_text)
			x += w + gap
		else:
			card_y = top_y - social_size
			_draw_rounded_card(c, x, card_y, social_size, social_size, 3, white)
			c.drawImage(social_qr_path, x + 1, card_y + 1, width=social_size - 2, height=social_size - 2,
				preserveAspectRatio=True, mask="auto")
			text_x = x + social_size + 6
			c.setFillColorRGB(1, 1, 1, alpha=0.85)
			c.setFont(FONT_BOLD, 7.5)
			c.drawString(text_x, top_y - 6, (gc_type.social_follow_text or "Follow us!").upper())
			c.setFillColor(white)
			c.setFont(FONT_BOLD, 9)
			c.drawString(text_x, top_y - 16, gc_type.social_label or "")
			x += w + gap


# --- drawing primitives ---------------------------------------------------

def _draw_rounded_card(c, x, y, w, h, radius, fill_color):
	c.setFillColorRGB(0, 0, 0, alpha=0.12)
	c.roundRect(x, y - 0.6, w, h, radius, fill=1, stroke=0)
	c.setFillColor(fill_color)
	c.roundRect(x, y, w, h, radius, fill=1, stroke=0)


def _draw_image_card(c, image_path, x, y, w, h):
	pad = 1.2 * mm
	_draw_rounded_card(c, x - pad, y - pad, w + 2 * pad, h + 2 * pad, 3, white)
	c.drawImage(image_path, x, y, width=w, height=h, preserveAspectRatio=True, mask="auto")


def _draw_dot_pattern(c, width_pt, height_pt):
	spacing = 4.5 * mm
	c.setFillColorRGB(1, 1, 1, alpha=0.28)
	radius = 0.45
	rows = int(height_pt / spacing) + 1
	cols = int(width_pt / spacing) + 1
	for row in range(rows):
		for col in range(cols):
			c.circle(col * spacing, row * spacing, radius, fill=1, stroke=0)


def _draw_gift_icon(c, cx, cy, half_size, color):
	c.setFillColor(color)
	box_w, box_h = half_size * 1.6, half_size * 1.1
	c.roundRect(cx - box_w / 2, cy - box_h / 2, box_w, box_h, 1, fill=1, stroke=0)
	c.setStrokeColor(color)
	c.setLineWidth(1.4)
	c.line(cx, cy - box_h / 2, cx, cy + box_h / 2)
	c.setFillColor(color)
	bow_r = half_size * 0.28
	c.circle(cx - bow_r * 0.9, cy + box_h / 2, bow_r, fill=1, stroke=0)
	c.circle(cx + bow_r * 0.9, cy + box_h / 2, bow_r, fill=1, stroke=0)


def _recipient_name(doc, gc_type):
	if doc.organization_name:
		return doc.organization_name
	if doc.first_name or doc.last_name:
		return f"{doc.first_name or ''} {doc.last_name or ''}".strip()
	return gc_type.default_recipient_text or ""


def _safe_color(hex_str, fallback):
	try:
		return HexColor(hex_str) if hex_str else HexColor(fallback)
	except Exception:
		return HexColor(fallback)


def _get_or_create_qr(data, assets_dir, prefix):
	if not data:
		return None
	filename = f"{prefix}_{hashlib.md5(data.encode()).hexdigest()[:12]}.png"
	path = os.path.join(assets_dir, filename)
	if os.path.exists(path):
		return path
	qr = qrcode.QRCode(box_size=10, border=1)
	qr.add_data(data)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	img.save(path)
	return path


def _get_or_create_barcode(data, assets_dir, barcode_type):
	if not data:
		return None
	filename = f"barcode_{barcode_type}_{hashlib.md5(data.encode()).hexdigest()[:12]}"
	path = os.path.join(assets_dir, filename + ".png")
	if os.path.exists(path):
		return path

	if not HAS_BARCODE:
		return _get_or_create_qr(data, assets_dir, "barcode_fallback")

	try:
		barcode_class = barcode.get_barcode_class(barcode_type)
		writer = ImageWriter()
		writer.dpi = 300
		obj = barcode_class(data, writer=writer)
		obj.save(os.path.join(assets_dir, filename), options={"write_text": False})
		return path
	except Exception:
		frappe.log_error(title="Gift Certificate barcode generation failed", message=frappe.get_traceback())
		return _get_or_create_qr(data, assets_dir, "barcode_fallback")


def _resolve_logo(logo_url, assets_dir):
	"""Resolve a Logo URL (site-relative file, this site's absolute URL, or
	an external URL) to a local file path reportlab can draw. Returns None
	on any failure so the header falls back to the badge icon."""
	if not logo_url:
		return None
	try:
		site_url = frappe.utils.get_url()
		relative = logo_url
		if relative.startswith(site_url):
			relative = relative[len(site_url):]

		if relative.startswith("/"):
			site_path = frappe.utils.get_site_path()
			rel = relative.lstrip("/")
			path = os.path.join(site_path, rel if rel.startswith("private/") else os.path.join("public", rel))
			return path if os.path.isfile(path) else None

		import requests
		cache_name = f"logo_{hashlib.md5(logo_url.encode()).hexdigest()[:12]}"
		ext = os.path.splitext(logo_url.split("?")[0])[1] or ".png"
		path = os.path.join(assets_dir, cache_name + ext)
		if os.path.exists(path):
			return path
		resp = requests.get(logo_url, timeout=5)
		resp.raise_for_status()
		with open(path, "wb") as f:
			f.write(resp.content)
		return path
	except Exception:
		frappe.log_error(title="Gift Certificate logo fetch failed", message=frappe.get_traceback())
		return None
