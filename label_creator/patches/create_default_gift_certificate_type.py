import frappe


def execute():
	"""
	Patch to create the default "Standard" Gift Certificate Type for existing installations
	"""
	if frappe.db.exists("Gift Certificate Type", "Standard"):
		return

	doc = frappe.get_doc({
		"doctype": "Gift Certificate Type",
		"gift_certificate_type_name": "Standard",
		"display_name": "Standard Gift Certificate",
		"page_size": "A6",
		"card_width_mm": 105,
		"card_height_mm": 148,
		"background_color": "#0b574d",
		"show_dot_pattern": 1,
		"accent_color_start": "#2dd4bf",
		"accent_color_end": "#0d9488",
		"title_text": "Gift Certificate",
		"tagline_text": "A little something meaningful, made with care.",
		"recipient_label": "Presented to:",
		"default_recipient_text": "Valued Recipient",
		"value_label": "Gift Value",
		"default_currency": "CAD",
		"code_label": "Code",
		"expiry_label": "Expires",
		"no_expiration_text": "No Expiration",
		"show_qr_code": 1,
		"qr_redeem_base_url": "https://erp.craftedgoods.ca/gift-certificate-redeem?code=",
		"qr_instruction_text": "Scan QR Code to Activate",
		"qr_position": "Flow (Below Value)",
		"qr_size_mm": 20,
		"show_barcode": 1,
		"barcode_type": "code128",
		"barcode_position": "Flow (Footer)",
		"barcode_height_mm": 8,
		"conditions_text": (
			"Scan to activate before use. Valid in-store only. "
			"Non-refundable and cannot be combined with other offers."
		),
		"show_footer_links": 1,
		"website_label": "craftedgoods.ca",
		"website_url": "https://craftedgoods.ca",
		"social_label": "crafted.shop",
		"social_url": "https://instagram.com/crafted.shop",
		"social_follow_text": "Follow us!",
		"social_qr_size_mm": 10,
		"provider": "Lightspeed",
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	print("Created default Gift Certificate Type: Standard")
