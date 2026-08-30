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


def _create_lightspeed_gift_card(base_url, headers, doc):
	"""
	Call 1 of 2: create the gift card in Lightspeed for the certificate's
	amount. A confirmed response is what "Activated" means for this
	certificate - the card now exists in Lightspeed and is usable, separate
	from who (if anyone) it ends up linked to.
	"""
	url = f"{base_url}/2.0/gift_cards"
	payload = {
		"number": doc.certificate_code,
		"amount": str(doc.amount),
		# expires_at is intentionally omitted/left empty - the gift
		# certificate's own expiration is tracked in the ERP, not mirrored
		# as a Lightspeed gift card expiry. time_zone/user_id are likewise
		# left out.
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

	return gift_card


def _find_lightspeed_customer(base_url, headers, email):
	"""Look up an existing Lightspeed customer by email. Returns the
	customer record, or None if no match is found."""
	url = f"{base_url}/2.0/customers"
	response = frappe.make_get_request(url, params={"email": email}, headers=headers)
	response = response if isinstance(response, dict) else {}
	customers = response.get("data") or []
	return customers[0] if customers else None


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
	customer = response.get("data") or {}
	if not customer.get("id"):
		frappe.throw(_("Lightspeed did not return a customer ID after creation."))
	return customer


def _link_lightspeed_customer(base_url, headers, doc):
	"""
	Call 2 of 2: find or create the redeemer's Lightspeed customer, and
	record the link on their ERPNext Customer record (custom_lightspeed_id /
	lightspeed_customer_code) so this and future redemptions reuse the same
	Lightspeed customer instead of creating duplicates. A confirmed link is
	what "Linked" means for this certificate.
	"""
	customer_doc = frappe.get_doc("Customer", doc.redeemed_by)

	if not customer_doc.get("custom_lightspeed_id"):
		lightspeed_customer = _find_lightspeed_customer(base_url, headers, doc.email) or \
			_create_lightspeed_customer(base_url, headers, doc)

		customer_doc.db_set("custom_lightspeed_id", lightspeed_customer.get("id"), commit=True)
		customer_doc.db_set(
			"lightspeed_customer_code", lightspeed_customer.get("customer_code"), commit=True
		)

	# Mirror the link onto the certificate itself so it's visible on the
	# Gift Certificate form, not just on the linked Customer record.
	doc.db_set(
		"lightspeed_customer_code", customer_doc.get("lightspeed_customer_code"), commit=True
	)

	return customer_doc


def _upsert_gift_card(doc, gift_card, customer_doc):
	"""
	Mirror the Lightspeed gift card locally as a Gift Card record, so it can
	be looked up/reported on without calling out to Lightspeed. Keyed by
	code (the gift card number), so re-redeeming the same certificate code
	updates the existing record instead of duplicating it.
	"""
	name = frappe.db.exists("Gift Card", doc.certificate_code)
	card = frappe.get_doc("Gift Card", name) if name else frappe.new_doc("Gift Card")

	card.code = doc.certificate_code
	card.gift_certificate = doc.name
	card.balance = gift_card.get("balance", doc.amount)
	card.status = gift_card.get("status") or "Active"
	card.created_at = gift_card.get("created_at") or frappe.utils.now_datetime()
	card.last_used = gift_card.get("last_used")
	card.customer = customer_doc.name

	card.save(ignore_permissions=True)


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

		gift_card = _create_lightspeed_gift_card(base_url, headers, doc)
		doc.db_set("status", "Activated", commit=True)

		customer_doc = _link_lightspeed_customer(base_url, headers, doc)
		doc.db_set("status", "Linked", commit=True)

		_upsert_gift_card(doc, gift_card, customer_doc)

		frappe.msgprint(
			_("Gift Card <b>{0}</b> successfully created in Lightspeed (Balance: {1})").format(
				doc.certificate_code, gift_card.get("balance")
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
