// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

// Keep in sync with PAGE_SIZES in gift_certificate_type.py
const PAGE_SIZES = {
	'A4': [210, 297],
	'A5': [148, 210],
	'A6': [105, 148],
	'Letter': [215.9, 279.4],
	'Legal': [215.9, 355.6]
};

frappe.ui.form.on('Gift Certificate Type', {
	page_size: function(frm) {
		const size = PAGE_SIZES[frm.doc.page_size];
		if (size) {
			frm.set_value('card_width_mm', size[0]);
			frm.set_value('card_height_mm', size[1]);
		}
	}
});
