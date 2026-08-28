# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

CERTIFICATE_CODE_PREFIX = "GC-"
CERTIFICATE_CODE_RANDOM_LENGTH = 10


class GiftCertificate(Document):
	def autoname(self):
		"""
		The certificate code doubles as the document's primary key, so it's
		generated here (autoname runs before validate) rather than assigned
		separately. Mirrors the client-side generator in gift_certificate.js.
		"""
		if not self.certificate_code:
			random_hash = frappe.utils.generate_hash(length=CERTIFICATE_CODE_RANDOM_LENGTH).upper()
			self.certificate_code = f"{CERTIFICATE_CODE_PREFIX}{random_hash}"

		self.name = self.certificate_code

	def validate(self):
		if self.amount is not None and self.amount <= 0:
			frappe.throw(_("Amount must be greater than 0"))

		if self.expiration and frappe.utils.getdate(self.expiration) < frappe.utils.getdate() and self.status not in (
			"Cancelled", "Expired"
		):
			frappe.msgprint(
				_("This certificate's expiration date is in the past."),
				indicator="orange",
				alert=True,
			)
