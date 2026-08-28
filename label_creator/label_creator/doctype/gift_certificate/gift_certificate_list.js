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

	// Rendered natively, one page per certificate at its own Gift
	// Certificate Type's size/design, combined into one PDF - see
	// utils/gift_certificate_pdf.py. Not Frappe's built-in
	// download_multi_pdf: that renders through the print/wkhtmltopdf
	// pipeline, which forces the page size from Print Settings (A4 by
	// default) regardless of the certificate's own configured size.
	const params = new URLSearchParams({
		names: JSON.stringify(names)
	});

	window.open(`/api/method/label_creator.api.gift_certificate.bulk_print_gift_certificates?${params.toString()}`);
}
