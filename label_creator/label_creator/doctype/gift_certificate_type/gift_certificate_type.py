# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class GiftCertificateType(Document):
	def validate(self):
		if self.card_width_mm <= 0:
			frappe.throw(_("Card width must be greater than 0"))
		if self.card_height_mm <= 0:
			frappe.throw(_("Card height must be greater than 0"))
		if self.show_qr_code and self.qr_size_mm <= 0:
			frappe.throw(_("QR size must be greater than 0"))
		if self.show_barcode and self.barcode_height_mm <= 0:
			frappe.throw(_("Barcode height must be greater than 0"))
