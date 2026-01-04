// Copyright (c) 2025, Your Company and contributors
// For license information, please see license.txt

frappe.ui.form.on('Label Type', {
	refresh: function(frm) {
		// Add custom button to preview label
		if (!frm.is_new()) {
			frm.add_custom_button(__('Preview Label'), function() {
				preview_label(frm);
			});
		}
		// Set initial field states based on offset mode
		toggle_offset_fields(frm);
	},

	offset_input_mode: function(frm) {
		toggle_offset_fields(frm);
	},

	label_width: function(frm) {
		// Recalculate X offset values when label width changes
		if (frm.doc.offset_input_mode === 'Inches') {
			// In Inches mode: update percentages based on inches
			update_percentage_from_inches(frm, 'qrcode_x_offset', 'qrcode_x_offset_pct', 'label_width');
			update_percentage_from_inches(frm, 'sku_x_offset', 'sku_x_offset_pct', 'label_width');
			update_percentage_from_inches(frm, 'product_name_x_offset', 'product_name_x_offset_pct', 'label_width');
			update_percentage_from_inches(frm, 'price_x_offset', 'price_x_offset_pct', 'label_width');
		} else {
			// In Percentage mode: update inches based on percentages
			update_inches_from_percentage(frm, 'qrcode_x_offset_pct', 'qrcode_x_offset', 'label_width');
			update_inches_from_percentage(frm, 'sku_x_offset_pct', 'sku_x_offset', 'label_width');
			update_inches_from_percentage(frm, 'product_name_x_offset_pct', 'product_name_x_offset', 'label_width');
			update_inches_from_percentage(frm, 'price_x_offset_pct', 'price_x_offset', 'label_width');
		}
	},

	label_height: function(frm) {
		// Recalculate Y offset values when label height changes
		if (frm.doc.offset_input_mode === 'Inches') {
			// In Inches mode: update percentages based on inches
			update_percentage_from_inches(frm, 'qrcode_y_offset', 'qrcode_y_offset_pct', 'label_height');
			update_percentage_from_inches(frm, 'sku_y_offset', 'sku_y_offset_pct', 'label_height');
			update_percentage_from_inches(frm, 'product_name_y_offset', 'product_name_y_offset_pct', 'label_height');
			update_percentage_from_inches(frm, 'price_y_offset', 'price_y_offset_pct', 'label_height');
		} else {
			// In Percentage mode: update inches based on percentages
			update_inches_from_percentage(frm, 'qrcode_y_offset_pct', 'qrcode_y_offset', 'label_height');
			update_inches_from_percentage(frm, 'sku_y_offset_pct', 'sku_y_offset', 'label_height');
			update_inches_from_percentage(frm, 'product_name_y_offset_pct', 'product_name_y_offset', 'label_height');
			update_inches_from_percentage(frm, 'price_y_offset_pct', 'price_y_offset', 'label_height');
		}
	},

	label_orientation: function(frm) {
		// Recalculate all offsets when orientation changes
		recalculate_all_offsets(frm);
	},

	labels_per_row: function(frm) {
		// Recalculate all offsets when layout changes
		recalculate_all_offsets(frm);
	},

	labels_per_column: function(frm) {
		// Recalculate all offsets when layout changes
		recalculate_all_offsets(frm);
	},

	page_width_inch: function(frm) {
		// Recalculate all offsets when page width changes
		recalculate_all_offsets(frm);
	},

	page_height_inch: function(frm) {
		// Recalculate all offsets when page height changes
		recalculate_all_offsets(frm);
	},

	margin_top: function(frm) {
		// Recalculate all offsets when margins change
		recalculate_all_offsets(frm);
	},

	margin_bottom: function(frm) {
		// Recalculate all offsets when margins change
		recalculate_all_offsets(frm);
	},

	margin_left: function(frm) {
		// Recalculate all offsets when margins change
		recalculate_all_offsets(frm);
	},

	margin_right: function(frm) {
		// Recalculate all offsets when margins change
		recalculate_all_offsets(frm);
	},

	// QR Code X Offset
	qrcode_x_offset: function(frm) {
		if (frm.doc.offset_input_mode === 'Inches') {
			update_percentage_from_inches(frm, 'qrcode_x_offset', 'qrcode_x_offset_pct', 'label_width');
		}
	},
	qrcode_x_offset_pct: function(frm) {
		if (frm.doc.offset_input_mode === 'Percentage') {
			update_inches_from_percentage(frm, 'qrcode_x_offset_pct', 'qrcode_x_offset', 'label_width');
		}
	},

	// QR Code Y Offset
	qrcode_y_offset: function(frm) {
		if (frm.doc.offset_input_mode === 'Inches') {
			update_percentage_from_inches(frm, 'qrcode_y_offset', 'qrcode_y_offset_pct', 'label_height');
		}
	},
	qrcode_y_offset_pct: function(frm) {
		if (frm.doc.offset_input_mode === 'Percentage') {
			update_inches_from_percentage(frm, 'qrcode_y_offset_pct', 'qrcode_y_offset', 'label_height');
		}
	},

	// SKU X Offset
	sku_x_offset: function(frm) {
		if (frm.doc.offset_input_mode === 'Inches') {
			update_percentage_from_inches(frm, 'sku_x_offset', 'sku_x_offset_pct', 'label_width');
		}
	},
	sku_x_offset_pct: function(frm) {
		if (frm.doc.offset_input_mode === 'Percentage') {
			update_inches_from_percentage(frm, 'sku_x_offset_pct', 'sku_x_offset', 'label_width');
		}
	},

	// SKU Y Offset
	sku_y_offset: function(frm) {
		if (frm.doc.offset_input_mode === 'Inches') {
			update_percentage_from_inches(frm, 'sku_y_offset', 'sku_y_offset_pct', 'label_height');
		}
	},
	sku_y_offset_pct: function(frm) {
		if (frm.doc.offset_input_mode === 'Percentage') {
			update_inches_from_percentage(frm, 'sku_y_offset_pct', 'sku_y_offset', 'label_height');
		}
	},

	// Product Name X Offset
	product_name_x_offset: function(frm) {
		if (frm.doc.offset_input_mode === 'Inches') {
			update_percentage_from_inches(frm, 'product_name_x_offset', 'product_name_x_offset_pct', 'label_width');
		}
	},
	product_name_x_offset_pct: function(frm) {
		if (frm.doc.offset_input_mode === 'Percentage') {
			update_inches_from_percentage(frm, 'product_name_x_offset_pct', 'product_name_x_offset', 'label_width');
		}
	},

	// Product Name Y Offset
	product_name_y_offset: function(frm) {
		if (frm.doc.offset_input_mode === 'Inches') {
			update_percentage_from_inches(frm, 'product_name_y_offset', 'product_name_y_offset_pct', 'label_height');
		}
	},
	product_name_y_offset_pct: function(frm) {
		if (frm.doc.offset_input_mode === 'Percentage') {
			update_inches_from_percentage(frm, 'product_name_y_offset_pct', 'product_name_y_offset', 'label_height');
		}
	},

	// Price X Offset
	price_x_offset: function(frm) {
		if (frm.doc.offset_input_mode === 'Inches') {
			update_percentage_from_inches(frm, 'price_x_offset', 'price_x_offset_pct', 'label_width');
		}
	},
	price_x_offset_pct: function(frm) {
		if (frm.doc.offset_input_mode === 'Percentage') {
			update_inches_from_percentage(frm, 'price_x_offset_pct', 'price_x_offset', 'label_width');
		}
	},

	// Price Y Offset
	price_y_offset: function(frm) {
		if (frm.doc.offset_input_mode === 'Inches') {
			update_percentage_from_inches(frm, 'price_y_offset', 'price_y_offset_pct', 'label_height');
		}
	},
	price_y_offset_pct: function(frm) {
		if (frm.doc.offset_input_mode === 'Percentage') {
			update_inches_from_percentage(frm, 'price_y_offset_pct', 'price_y_offset', 'label_height');
		}
	}
});

function toggle_offset_fields(frm) {
	const mode = frm.doc.offset_input_mode || 'Inches';
	const offset_fields = [
		'qrcode_x_offset', 'qrcode_y_offset',
		'sku_x_offset', 'sku_y_offset',
		'product_name_x_offset', 'product_name_y_offset',
		'price_x_offset', 'price_y_offset'
	];
	const pct_fields = [
		'qrcode_x_offset_pct', 'qrcode_y_offset_pct',
		'sku_x_offset_pct', 'sku_y_offset_pct',
		'product_name_x_offset_pct', 'product_name_y_offset_pct',
		'price_x_offset_pct', 'price_y_offset_pct'
	];

	if (mode === 'Inches') {
		// Enable inch fields, disable percentage fields
		offset_fields.forEach(field => {
			frm.set_df_property(field, 'read_only', 0);
		});
		pct_fields.forEach(field => {
			frm.set_df_property(field, 'read_only', 1);
		});
	} else {
		// Enable percentage fields, disable inch fields
		offset_fields.forEach(field => {
			frm.set_df_property(field, 'read_only', 1);
		});
		pct_fields.forEach(field => {
			frm.set_df_property(field, 'read_only', 0);
		});
	}
	frm.refresh_fields();
}

function update_percentage_from_inches(frm, inch_field, pct_field, dimension_field) {
	const inch_value = frm.doc[inch_field] || 0;
	const dimension = frm.doc[dimension_field] || 1;

	if (dimension > 0) {
		const pct_value = (inch_value / dimension) * 100;
		frm.set_value(pct_field, parseFloat(pct_value.toFixed(2)));
	}
}

function update_inches_from_percentage(frm, pct_field, inch_field, dimension_field) {
	const pct_value = frm.doc[pct_field] || 0;
	const dimension = frm.doc[dimension_field] || 1;

	const inch_value = (pct_value / 100) * dimension;
	frm.set_value(inch_field, parseFloat(inch_value.toFixed(4)));
}

function recalculate_all_offsets(frm) {
	// Recalculate both X and Y offsets for all elements
	if (frm.doc.offset_input_mode === 'Inches') {
		// In Inches mode: update percentages based on inches
		// X offsets (based on label width)
		update_percentage_from_inches(frm, 'qrcode_x_offset', 'qrcode_x_offset_pct', 'label_width');
		update_percentage_from_inches(frm, 'sku_x_offset', 'sku_x_offset_pct', 'label_width');
		update_percentage_from_inches(frm, 'product_name_x_offset', 'product_name_x_offset_pct', 'label_width');
		update_percentage_from_inches(frm, 'price_x_offset', 'price_x_offset_pct', 'label_width');

		// Y offsets (based on label height)
		update_percentage_from_inches(frm, 'qrcode_y_offset', 'qrcode_y_offset_pct', 'label_height');
		update_percentage_from_inches(frm, 'sku_y_offset', 'sku_y_offset_pct', 'label_height');
		update_percentage_from_inches(frm, 'product_name_y_offset', 'product_name_y_offset_pct', 'label_height');
		update_percentage_from_inches(frm, 'price_y_offset', 'price_y_offset_pct', 'label_height');
	} else {
		// In Percentage mode: update inches based on percentages
		// X offsets (based on label width)
		update_inches_from_percentage(frm, 'qrcode_x_offset_pct', 'qrcode_x_offset', 'label_width');
		update_inches_from_percentage(frm, 'sku_x_offset_pct', 'sku_x_offset', 'label_width');
		update_inches_from_percentage(frm, 'product_name_x_offset_pct', 'product_name_x_offset', 'label_width');
		update_inches_from_percentage(frm, 'price_x_offset_pct', 'price_x_offset', 'label_width');

		// Y offsets (based on label height)
		update_inches_from_percentage(frm, 'qrcode_y_offset_pct', 'qrcode_y_offset', 'label_height');
		update_inches_from_percentage(frm, 'sku_y_offset_pct', 'sku_y_offset', 'label_height');
		update_inches_from_percentage(frm, 'product_name_y_offset_pct', 'product_name_y_offset', 'label_height');
		update_inches_from_percentage(frm, 'price_y_offset_pct', 'price_y_offset', 'label_height');
	}
}

function preview_label(frm) {
	// Save the document first to ensure all changes are persisted
	if (frm.is_dirty()) {
		frappe.show_alert({
			message: __('Saving changes first...'),
			indicator: 'blue'
		});
		frm.save().then(() => {
			generate_preview(frm);
		});
	} else {
		generate_preview(frm);
	}
}

function generate_preview(frm) {
	// Show loading message
	frappe.show_alert({
		message: __('Generating preview...'),
		indicator: 'blue'
	});

	// Call API with just the label type name - it will use the shared config builder
	frappe.call({
		method: 'label_creator.api.labels.preview_label',
		args: {
			label_type_name: frm.doc.name
		},
		callback: function(r) {
			if (r.message && r.message.success) {
				// Create a dialog to show the preview
				const d = new frappe.ui.Dialog({
					title: __('Label Preview - ') + frm.doc.display_name,
					size: 'extra-large',
					fields: [
						{
							fieldtype: 'HTML',
							fieldname: 'preview_html'
						}
					]
				});

				let html = '';

				// Check if we have image data or PDF data
				if (r.message.image_data) {
					// Display as PNG image
					html = `
						<div style="text-align: center; padding: 20px;">
							<p style="margin-bottom: 15px; color: #666;">
								<strong>Page Layout Preview</strong><br>
								Labels per Row: ${frm.doc.labels_per_row}, Labels per Column: ${frm.doc.labels_per_column}<br>
								Page Size: ${frm.doc.page_width_inch}" × ${frm.doc.page_height_inch}"
							</p>
							<div style="overflow: auto; max-height: 700px; border: 1px solid #ddd; border-radius: 4px; padding: 10px; background: #f5f5f5;">
								<img
									src="data:image/png;base64,${r.message.image_data}"
									style="max-width: 100%; height: auto; display: block; margin: 0 auto; background: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1);"
									alt="Label Preview">
							</div>
							<p style="margin-top: 15px; color: #888; font-size: 12px;">
								<strong>Sample Data:</strong> SKU: ${frm.doc.sku_sample || 'SAM-PLE-SKU'}, Product: ${frm.doc.product_name_sample || 'Sample Product'}, Price: ${frm.doc.price_sample || '29.99'}<br>
								Preview shows full page with all labels based on current configuration
							</p>
						</div>
					`;
				} else if (r.message.pdf_data) {
					// Fallback to PDF iframe
					html = `
						<div style="text-align: center; padding: 20px;">
							<p style="margin-bottom: 15px; color: #666;">
								<strong>Sample Data:</strong> SKU: ${frm.doc.sku_sample || 'SAM-PLE-SKU'}, Product: ${frm.doc.product_name_sample || 'Sample Product'}, Price: ${frm.doc.price_sample || '29.99'}
							</p>
							<iframe
								src="data:application/pdf;base64,${r.message.pdf_data}"
								style="width: 100%; height: 600px; border: 1px solid #ddd; border-radius: 4px;"
								frameborder="0">
							</iframe>
							<p style="margin-top: 15px; color: #888; font-size: 12px;">
								Preview shows page layout with all labels. Install PyMuPDF for image preview.
							</p>
						</div>
					`;
				}

				d.fields_dict.preview_html.$wrapper.html(html);
				d.show();

				frappe.show_alert({
					message: __('Preview generated successfully'),
					indicator: 'green'
				});
			} else {
				frappe.msgprint({
					title: __('Error'),
					message: r.message.message || __('Failed to generate preview'),
					indicator: 'red'
				});
			}
		},
		error: function(err) {
			frappe.msgprint({
				title: __('Error'),
				message: __('Failed to generate preview. Please check your configuration.'),
				indicator: 'red'
			});
		}
	});
}
