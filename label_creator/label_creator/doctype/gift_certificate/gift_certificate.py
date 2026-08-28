# Copyright (c) 2026, Your Company and contributors
# For license information, please see license.txt

import secrets
import string

import frappe
from frappe import _
from frappe.model.document import Document

CERTIFICATE_CODE_LENGTH = 12
CERTIFICATE_CODE_ALPHABET = string.ascii_uppercase + string.digits


class GiftCertificate(Document):
	def validate(self):
		if not self.certificate_code:
			self.certificate_code = generate_certificate_code()

		if self.amount is not None and self.amount <= 0:
			frappe.throw(_("Amount must be greater than 0"))

		if self.expiration and self.expiration < frappe.utils.nowdate() and self.status not in (
			"Cancelled", "Expired"
		):
			frappe.msgprint(
				_("This certificate's expiration date is in the past."),
				indicator="orange",
				alert=True,
			)


def generate_certificate_code():
	"""Generate a unique, human-friendly certificate code."""
	for _attempt in range(10):
		code = "".join(secrets.choice(CERTIFICATE_CODE_ALPHABET) for _ in range(CERTIFICATE_CODE_LENGTH))
		if not frappe.db.exists("Gift Certificate", {"certificate_code": code}):
			return code

	frappe.throw(_("Could not generate a unique certificate code. Please try saving again."))
