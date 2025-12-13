import frappe
from frappe import _


def after_install():
    """
    Setup Label Creator after installation
    """
    create_label_creator_web_page()


def create_label_creator_web_page():
    """
    Create or update the Label Creator web page for sidebar navigation
    """
    try:
        # Check if web page already exists
        if frappe.db.exists("Web Page", "label-creator"):
            doc = frappe.get_doc("Web Page", "label-creator")
        else:
            doc = frappe.new_doc("Web Page")
            doc.name = "label-creator"
            doc.route = "label-creator"

        # Update fields
        doc.title = "Label Creator"
        doc.published = 1
        doc.show_sidebar = 1
        doc.content_type = "Page Builder"
        doc.main_section = "<h3>Label Creator</h3><p>Generate professional product labels with QR codes</p>"
        doc.meta_title = "Label Creator"
        doc.meta_description = "Create professional product labels with QR codes for your inventory"

        doc.save(ignore_permissions=True)
        frappe.db.commit()

        frappe.logger().info("Label Creator web page created/updated successfully")

    except Exception as e:
        frappe.logger().error(f"Error creating Label Creator web page: {str(e)}")
        frappe.log_error(frappe.get_traceback(), "Label Creator Installation Error")
