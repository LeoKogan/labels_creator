import frappe
from frappe import _


def activate_gift_certificate(doc):
	"""
	Called when a Gift Certificate is redeemed (see
	label_creator.api.gift_certificate.register_gift_certificate) -
	deliberately not on creation, since staff may print and hand out a
	certificate well before anyone redeems it.

	Dispatches to the activation provider configured on the certificate's
	Gift Certificate Type, if any. Adding a new provider later just means
	writing another `_activate_<provider>(doc)` function and registering it
	below - nothing about the Gift Certificate doctype or the redemption
	flow needs to change.
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


def _find_lightspeed_customer(base_url, headers, email):
	"""Look up an existing Lightspeed customer by email. Returns the
	customer id, or None if no match is found."""
	url = f"{base_url}/2.0/customers"
	response = frappe.make_get_request(url, params={"email": email}, headers=headers)
	response = response if isinstance(response, dict) else {}
	customers = response.get("data") or []
	return customers[0].get("id") if customers else None


def _create_lightspeed_customer(base_url, headers, doc):
	"""Create a new Lightspeed customer from the redeemer's details."""
	url = f"{base_url}/2.0/customers"
	payload = {
		"first_name": doc.first_name,
		"last_name": doc.last_name,
		"email": doc.email,
		"phone": doc.phone_number,
	}
	response = frappe.make_post_request(url, json=payload, headers=headers)
	response = response if isinstance(response, dict) else {}
	customer_id = (response.get("data") or {}).get("id")
	if not customer_id:
		frappe.throw(_("Lightspeed did not return a customer ID after creation."))
	return customer_id


def _get_or_create_lightspeed_customer(base_url, headers, doc):
	customer_id = _find_lightspeed_customer(base_url, headers, doc.email)
	if customer_id:
		return customer_id
	return _create_lightspeed_customer(base_url, headers, doc)


def _activate_lightspeed(doc):
	try:
		token, base_url = get_provider_credentials("Lightspeed")
		if not token or not base_url:
			frappe.throw(
				_("Lightspeed credentials not found. Please configure them in Custom API Settings.")
			)

		headers = {
			"Authorization": f"Bearer {token}",
			"Content-Type": "application/json",
			"Accept": "application/json",
		}

		# Look up the redeemer in Lightspeed by email and create them there
		# if they've never been seen before. The gift_cards endpoint has no
		# customer_id field to link against, so this only ensures the
		# customer record exists - it doesn't attach it to the card itself.
		_get_or_create_lightspeed_customer(base_url, headers, doc)

		url = f"{base_url}/2.0/gift_cards"
		payload = {
			"number": doc.certificate_code,
			"amount": str(doc.amount),
			# expires_at is intentionally omitted/left empty - the gift
			# certificate's own expiration is tracked in the ERP, not mirrored
			# as a Lightspeed gift card expiry.
		}

		data = frappe.make_post_request(url, json=payload, headers=headers)
		data = data if isinstance(data, dict) else {}
		gift_card = data.get("data") or {}

		# Lightspeed responding 200 isn't proof the card exists - only a
		# returned id/number confirms it. Without that, treat this as a
		# failure so it surfaces below rather than silently reporting success.
		if not (gift_card.get("id") or gift_card.get("number")):
			frappe.throw(
				_("Lightspeed did not confirm creation of gift card {0}.").format(doc.certificate_code)
			)

		balance = gift_card.get("balance")

		frappe.msgprint(
			_("Gift Card <b>{0}</b> successfully created in Lightspeed (Balance: {1})").format(
				doc.certificate_code, balance
			),
			indicator="green",
			alert=True,
		)

	except Exception as e:
		frappe.log_error(
			title="Lightspeed gift card activation failed",
			message=_(
				"Could not activate gift card {0} in Lightspeed for {1} {2} <{3}>.\n\n{4}"
			).format(
				doc.certificate_code, doc.first_name, doc.last_name, doc.email, frappe.get_traceback()
			),
		)
		frappe.msgprint(
			_("Gift certificate redeemed in ERP, but Lightspeed gift card creation failed: {0}").format(e),
			indicator="orange",
			alert=True,
		)


# Register new providers here as they come online, e.g. "Square": _activate_square
PROVIDER_HANDLERS = {
	"Lightspeed": _activate_lightspeed,
}
