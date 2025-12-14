import frappe
from frappe import _


def after_install():
    """
    Setup Label Creator after installation
    """
    add_to_website_sidebar()


def add_to_website_sidebar():
    """
    Add Label Creator link to website sidebar
    """
    try:
        # Get or create Website Settings
        if not frappe.db.exists("Website Settings", "Website Settings"):
            return

        website_settings = frappe.get_doc("Website Settings", "Website Settings")

        # Check if the link already exists
        existing = False
        for item in website_settings.top_bar_items:
            if item.url == "/label-creator":
                existing = True
                break

        if not existing:
            # Add Label Creator to top bar
            website_settings.append("top_bar_items", {
                "label": "Label Creator",
                "url": "/label-creator",
                "right": 0
            })
            website_settings.save(ignore_permissions=True)
            frappe.db.commit()

        frappe.logger().info("Label Creator added to website navigation")

    except Exception as e:
        frappe.logger().error(f"Error adding Label Creator to website: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Label Creator Installation Error")
