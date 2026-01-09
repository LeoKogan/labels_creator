frappe.pages['label-creator'].on_page_load = function(wrapper) {
	// Redirect to the web version which has all the latest features
	// This ensures /app/label-creator and /label-creator show the same page
	window.location.href = '/label-creator';
};
