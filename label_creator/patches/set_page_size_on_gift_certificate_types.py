import frappe

from label_creator.label_creator.doctype.gift_certificate_type.gift_certificate_type import PAGE_SIZES


def execute():
	"""
	Backfill the new required "Page Size" field on existing Gift Certificate
	Type records (e.g. "Standard", created by an earlier patch before this
	field existed). Match against known presets by dimensions; anything that
	doesn't match a preset falls back to "Custom" so its existing width/
	height are left untouched.
	"""
	if not frappe.db.table_exists("Gift Certificate Type"):
		return

	for row in frappe.get_all(
		"Gift Certificate Type", fields=["name", "page_size", "card_width_mm", "card_height_mm"]
	):
		if row.page_size:
			continue

		match = next(
			(
				size
				for size, (width, height) in PAGE_SIZES.items()
				if abs((row.card_width_mm or 0) - width) < 0.1
				and abs((row.card_height_mm or 0) - height) < 0.1
			),
			"Custom",
		)
		frappe.db.set_value("Gift Certificate Type", row.name, "page_size", match, update_modified=False)

	frappe.db.commit()
