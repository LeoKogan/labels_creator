// Copyright (c) 2025, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on('Label Type', {
	refresh: function(frm) {
		// Add custom button to preview label
		if (!frm.is_new()) {
			frm.add_custom_button(__('Preview Label'), function() {
				frappe.msgprint(__('Label preview feature coming soon'));
			});
		}
	}
});
