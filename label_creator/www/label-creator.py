import frappe

def get_context(context):
    """Context for label creator web page"""
    context.no_cache = 1

    # Check if user is logged in (allow all logged-in users, including website users)
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/label-creator"
        raise frappe.Redirect

    context.title = "Label Creator"

    return context
