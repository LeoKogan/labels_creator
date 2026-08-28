# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

# Standard portrait page sizes in millimeters (width, height). Keep in sync
# with the PAGE_SIZES map in gift_certificate_type.js.
PAGE_SIZES = {
	"A4": (210, 297),
	"A5": (148, 210),
	"A6": (105, 148),
	"Letter": (215.9, 279.4),
	"Legal": (215.9, 355.6),
}


class GiftCertificateType(Document):
	def validate(self):
		if self.page_size in PAGE_SIZES:
			self.card_width_mm, self.card_height_mm = PAGE_SIZES[self.page_size]

		if self.card_width_mm <= 0:
			frappe.throw(_("Card width must be greater than 0"))
		if self.card_height_mm <= 0:
			frappe.throw(_("Card height must be greater than 0"))
		if self.show_qr_code and self.qr_size_mm <= 0:
			frappe.throw(_("QR size must be greater than 0"))
		if self.show_barcode and self.barcode_height_mm <= 0:
			frappe.throw(_("Barcode height must be greater than 0"))
