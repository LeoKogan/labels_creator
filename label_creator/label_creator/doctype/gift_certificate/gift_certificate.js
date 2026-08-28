// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gift Certificate', {
	refresh: function(frm) {
		const status_colors = {
			Created: 'blue',
			Activated: 'green',
			Linked: 'purple',
			Suspended: 'orange',
			Cancelled: 'red',
			Expired: 'grey'
		};
		if (frm.doc.status) {
			frm.page.set_indicator(frm.doc.status, status_colors[frm.doc.status] || 'grey');
		}

		if (!frm.is_new()) {
			frm.add_custom_button(__('Print Certificate'), function() {
				frappe.route_options = { print_format: 'Gift Certificate' };
				frm.print_doc();
			});
		}
	}
});
