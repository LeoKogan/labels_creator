from . import __version__ as app_version

app_name = "label_creator"
app_title = "Label Creator"
app_publisher = "Your Company"
app_description = "Design professional product labels with QR codes for ERPNext"
app_email = "info@yourcompany.com"
app_license = "MIT"

# Website
# --------

# Add to website context
website_context = {
    "brand_html": "Label Creator"
}

# Add custom route to website sidebar
# This adds the Label Creator link to the sidebar without creating a Web Page
website_route_rules = [
    {"from_route": "/label-creator", "to_route": "label-creator"},
]

# Portal menu items - Removed to keep Label Creator only in sidebar menu
# portal_menu_items = [
#     {
#         "title": "Labels",
#         "route": "/label-creator",
#         "reference_doctype": "",
#         "role": "All"
#     }
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/label_creator/css/label_creator.css"
# app_include_js = "/assets/label_creator/js/label_creator.js"

# include js, css files in header of web template
# web_include_css = "/assets/label_creator/css/label_creator.css"
# web_include_js = "/assets/label_creator/js/label_creator.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "label_creator/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
#	"methods": "label_creator.utils.jinja_methods",
#	"filters": "label_creator.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "label_creator.install.before_install"
after_install = "label_creator.install.install.after_install"

# Fixtures
# --------

fixtures = [
	{
		"dt": "Workspace",
		"filters": [
			["name", "=", "Labels"]
		]
	}
]

# Uninstallation
# ------------

# before_uninstall = "label_creator.uninstall.before_uninstall"
# after_uninstall = "label_creator.uninstall.after_uninstall"

# Desk Notifications
# -------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "label_creator.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"label_creator.tasks.all"
#	],
#	"daily": [
#		"label_creator.tasks.daily"
#	],
#	"hourly": [
#		"label_creator.tasks.hourly"
#	],
#	"weekly": [
#		"label_creator.tasks.weekly"
#	],
#	"monthly": [
#		"label_creator.tasks.monthly"
#	],
# }

# Testing
# -------

# before_tests = "label_creator.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "label_creator.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "label_creator.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

# user_data_fields = [
#	{
#		"doctype": "{doctype_1}",
#		"filter_by": "{filter_by}",
#		"redact_fields": ["{field_1}", "{field_2}"],
#		"partial": 1,
#	},
#	{
#		"doctype": "{doctype_2}",
#		"filter_by": "{filter_by}",
#		"strict": False,
#	},
#	{
#		"doctype": "{doctype_3}",
#		"partial": 1,
#	},
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"label_creator.auth.validate"
# ]
