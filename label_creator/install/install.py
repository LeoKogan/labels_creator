import frappe
from frappe import _


def after_install():
    """
    Setup Label Creator after installation
    """
    create_page_if_not_exists()


def create_page_if_not_exists():
    """
    Ensure the Label Creator page exists
    """
    try:
        if not frappe.db.exists("Page", "label-creator"):
            frappe.logger().info("Label Creator page will be created from page definition")
        else:
            frappe.logger().info("Label Creator page already exists")

    except Exception as e:
        frappe.logger().error(f"Error checking Label Creator page: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Label Creator Installation Error")
