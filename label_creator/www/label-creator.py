import frappe

def get_context(context):
    """Context for label creator web page"""
    context.no_cache = 1

    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.throw("Please login to access Label Creator", frappe.PermissionError)

    context.title = "Label Creator"

    return context
