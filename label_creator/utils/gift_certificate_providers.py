import frappe
from frappe import _


def activate_gift_certificate(doc, method=None):
	"""
	doc_event handler (Gift Certificate: after_insert). Dispatches to the
	activation provider configured on the certificate's Gift Certificate
	Type, if any. Adding a new provider later just means writing another
	`_activate_<provider>(doc)` function and registering it below - nothing
	about the Gift Certificate doctype or this hook needs to change.
	"""
	if not doc.gift_certificate_type:
		return

	provider = frappe.db.get_value("Gift Certificate Type", doc.gift_certificate_type, "provider")
	handler = PROVIDER_HANDLERS.get(provider)
	if not handler:
		return

	try:
		handler(doc)
	except Exception:
		# Activation is a best-effort side effect on top of the Gift
		# Certificate record - a provider/credentials problem (e.g. Custom
		# API Settings not configured on this site) must never block the
		# certificate itself from being saved. Each handler already reports
		# its own failures via msgprint; this is just a safety net in case
		# one doesn't.
		frappe.log_error(
			title=f"{provider} gift certificate activation failed",
			message=frappe.get_traceback(),
		)


def get_provider_credentials(service_name):
	"""
	Look up API credentials for a named service from the "Custom API
	Settings" doctype - a shared integration-credentials store already used
	elsewhere on this site, keyed by service name. Returns (None, None) if
	the doctype doesn't exist on this site or no matching, enabled,
	fully-configured row is found.
	"""
	if not frappe.db.table_exists("Custom API Settings"):
		return None, None

	for settings_row in frappe.get_all("Custom API Settings", fields=["name"]):
		settings = frappe.get_doc("Custom API Settings", settings_row.name)
		for row in settings.get("api_keys") or []:
			if row.service_name == service_name and row.enabled:
				token = row.get_password("api_key")
				base_url = (row.base_url or "").rstrip("/")
				if token and base_url:
					return token, base_url

	return None, None


def _activate_lightspeed(doc):
	try:
		token, base_url = get_provider_credentials("Lightspeed")
		if not token or not base_url:
			frappe.throw(
				_("Lightspeed credentials not found. Please configure them in Custom API Settings.")
			)

		url = f"{base_url}/2.0/gift_cards"
		payload = {
			"number": doc.certificate_code,
			"amount": str(doc.amount),
		}
		headers = {
			"Authorization": f"Bearer {token}",
			"Content-Type": "application/json",
			"Accept": "application/json",
		}

		data = frappe.make_post_request(url, json=payload, headers=headers)
		data = data if isinstance(data, dict) else {}
		balance = (data.get("data") or {}).get("balance")

		frappe.db.set_value("Gift Certificate", doc.name, "status", "Activated", update_modified=False)
		frappe.msgprint(
			_("Gift Card <b>{0}</b> successfully created in Lightspeed (Balance: {1})").format(
				doc.certificate_code, balance
			),
			indicator="green",
			alert=True,
		)

	except Exception as e:
		frappe.log_error(title="Lightspeed gift card create failed", message=frappe.get_traceback())
		frappe.msgprint(
			_("Gift Certificate saved in ERP. Lightspeed create failed: {0}").format(e),
			indicator="orange",
			alert=True,
		)


# Register new providers here as they come online, e.g. "Square": _activate_square
PROVIDER_HANDLERS = {
	"Lightspeed": _activate_lightspeed,
}
