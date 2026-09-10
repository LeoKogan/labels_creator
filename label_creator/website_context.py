import frappe


def update_website_context(context):
    """Only show Label Creator brand on Label Creator website routes."""
    path = ""
    try:
        path = frappe.request.path or ""
    except Exception:
        path = ""
    if path.startswith("/label-creator") or path.rstrip("/") == "/label-creator":
        context["brand_html"] = "Label Creator"
    elif context.get("brand_html") == "Label Creator":
        # clear pollution if another hook left it
        context["brand_html"] = context.get("app_name") or "Crafted"
