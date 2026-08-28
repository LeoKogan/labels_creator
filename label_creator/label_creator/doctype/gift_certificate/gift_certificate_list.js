// Copyright (c) 2026, Your Company and contributors
// For license information, please see license.txt

frappe.listview_settings['Gift Certificate'] = {
	onload(listview) {
		listview.page.add_actions_menu_item(
			__('Bulk Print Certificates'),
			() => bulk_print_gift_certificates(listview),
			false
		);
	}
};

function bulk_print_gift_certificates(listview) {
	const names = listview.get_checked_items(true);

	if (!names.length) {
		frappe.msgprint(__('Select at least one Gift Certificate to print.'));
		return;
	}

	// Each certificate renders through the Gift Certificate print format,
	// which reads its own linked Gift Certificate Type (page size, colors,
	// QR/barcode placement) at render time - so a mixed selection of types
	// still merges correctly into one PDF, each certificate keeping its own
	// look. no_letterhead=1 since the print format is a full custom card.
	const params = new URLSearchParams({
		doctype: 'Gift Certificate',
		name: JSON.stringify(names),
		format: 'Gift Certificate',
		no_letterhead: '1'
	});

	window.open(`/api/method/frappe.utils.print_format.download_multi_pdf?${params.toString()}`);
}
