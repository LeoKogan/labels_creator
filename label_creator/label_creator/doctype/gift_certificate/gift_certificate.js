// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on('Gift Certificate', {
	validate: function(frm) {
		// Only run for new local docs or if code is empty
		if (frm.doc.__islocal || !frm.doc.certificate_code) {
			let prefix = 'GC-';
			let randomLength = 10;
			let randomPart = frappe.utils.get_random(randomLength).toUpperCase();
			let code = prefix + randomPart;

			// Allow writing temporarily, set value, then make read-only
			frm.set_df_property('certificate_code', 'read_only', 0);
			frm.set_value('certificate_code', code);
			frm.set_df_property('certificate_code', 'read_only', 1);
		}
	},

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
