# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class LabelType(Document):
	def validate(self):
		"""Validate label type settings"""
		# Ensure positive dimensions
		if self.label_width <= 0:
			frappe.throw("Label width must be greater than 0")
		if self.label_height <= 0:
			frappe.throw("Label height must be greater than 0")
		if self.labels_per_row <= 0:
			frappe.throw("Labels per row must be greater than 0")
		if self.labels_per_column <= 0:
			frappe.throw("Labels per column must be greater than 0")
		if self.page_width_inch <= 0:
			frappe.throw("Page width must be greater than 0")
		if self.page_height_inch <= 0:
			frappe.throw("Page height must be greater than 0")
