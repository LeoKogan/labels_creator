import re

import frappe
from frappe import _
from frappe.integrations.utils import make_get_request, make_post_request

# Matches the version segment Lightspeed's Retail API requires at the end
# of the Base URL - either a dated version like ".../api/2026-07" or the
# legacy ".../api/2.0". Used to catch a Base URL that's missing/dropped this
# segment before it turns into a confusing 404 from Lightspeed itself (see
# get_provider_credentials()).
LIGHTSPEED_VERSIONED_BASE_URL_RE = re.compile(r"/(\d{4}-\d{2}|\d+\.\d+)$")

# Matches a bare version like "2026-07" or "2.0", to validate the API Key
# Detail row's own `api_version` field when present.
LIGHTSPEED_API_VERSION_RE = re.compile(r"^(\d{4}-\d{2}|\d+\.\d+)$")


def _console_log(label, data):
	"""
	Print the Lightspeed transaction data to the server console (stdout),
	visible in `bench start`/worker logs - in addition to the Error Log
	entry written on failure, so the request/response for a redemption can
	be watched live while debugging, not just found after the fact.
	"""
	print(f"[Gift Certificate / Lightspeed] {label}:\n{frappe.as_json(data, indent=2)}")


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

	Returns True if the certificate is now genuinely usable (either no
	provider is configured, so there's nothing to report, or the provider
	confirms the underlying gift card was created) and False if activation
	was attempted but failed - the caller uses this to tell the customer to
	reach out for help instead of claiming success. Anything past that point
	(e.g. linking the redeemer to a POS customer record) is the provider's
	own internal bookkeeping: it's never allowed to flip this back to False,
	only logged for staff to follow up on.
	"""
	if not doc.gift_certificate_type:
		return True

	provider = frappe.db.get_value("Gift Certificate Type", doc.gift_certificate_type, "provider")
	handler = PROVIDER_HANDLERS.get(provider)
	if not handler:
		return True

	try:
		return handler(doc)
	except Exception:
		# A provider/credentials problem (e.g. Custom API Settings not
		# configured on this site) must never block the certificate record
		# itself from being saved - the ERP-side redemption already
		# happened by the time this runs. Each handler already reports its
		# own failures via log_error/msgprint; this is just a safety net in
		# case one doesn't.
		frappe.log_error(
			title=f"{provider} gift certificate activation failed",
			message=frappe.get_traceback(),
		)
		return False


def get_provider_credentials(service_name):
	"""
	Look up API credentials for a named service from the "Custom API
	Settings" doctype - a shared integration-credentials store already used
	elsewhere on this site, keyed by service name. Returns (None, None) if
	the doctype doesn't exist on this site or no matching, enabled,
	fully-configured row is found.

	For "Lightspeed", the returned base_url has the API version segment
	applied, e.g. "https://crafted.retail.lightspeed.app/api/2026-07" (or
	the legacy "https://crafted.retail.lightspeed.app/api/2.0" - both are
	accepted by Lightspeed). The version comes from the API Key Detail
	row's own `api_version` field when that field is present and filled in
	(e.g. "2026-07" or "2.0"); otherwise it must already be the last
	segment of Base URL, for sites where that field doesn't exist.
	"""
	if not frappe.db.table_exists("Custom API Settings"):
		return None, None

	for settings_row in frappe.get_all("Custom API Settings", fields=["name"]):
		settings = frappe.get_doc("Custom API Settings", settings_row.name)
		for row in settings.get("api_keys") or []:
			if row.service_name == service_name and row.enabled:
				token = row.get_password("api_key")
				base_url = (row.base_url or "").strip().rstrip("/")
				if token and base_url:
					if service_name == "Lightspeed":
						base_url = _lightspeed_versioned_base_url(row, base_url)
					return token, base_url

	return None, None


def _lightspeed_versioned_base_url(row, base_url):
	"""
	Append the API Key Detail row's `api_version` (e.g. "2026-07") to
	base_url if that field exists and is filled in. Otherwise, fall back to
	requiring the version already be the last segment of base_url, and fail
	loudly rather than let a missing/blank version silently 404 every
	Lightspeed request.
	"""
	api_version = (row.get("api_version") or "").strip()
	if api_version:
		if not LIGHTSPEED_API_VERSION_RE.match(api_version):
			frappe.throw(
				_(
					"Lightspeed API Version in Custom API Settings is not a recognized "
					"version (expected e.g. 2026-07 or 2.0) - got {0}."
				).format(api_version)
			)
		return f"{base_url}/{api_version}"

	if not LIGHTSPEED_VERSIONED_BASE_URL_RE.search(base_url):
		frappe.throw(
			_(
				"Lightspeed Base URL in Custom API Settings is missing its API version "
				"segment (e.g. .../api/2026-07 or .../api/2.0) - got {0}. Without it, "
				"every request 404s against Lightspeed. Either set API Version on the "
				"row, or add the version segment to Base URL, and try again."
			).format(base_url)
		)
	return base_url


def _unwrap_lightspeed_object(response):
	"""
	Lightspeed's dated API versions (e.g. 2026-07) wrap a single-object
	response as {"data": {...}}, but the legacy 2.0 version returns the
	object flat - confirmed against a real POST /gift_cards response on
	2.0 that had no "data" key at all. Handle both so callers don't
	silently treat a real object as "not found" just because it wasn't
	wrapped.
	"""
	response = response if isinstance(response, dict) else {}
	data = response.get("data")
	return data if isinstance(data, dict) else response


def _create_lightspeed_gift_card(base_url, headers, doc):
	"""
	Call 1 of 2: create the gift card in Lightspeed for the certificate's
	amount. A confirmed response is what "Activated" means for this
	certificate - the card now exists in Lightspeed and is usable, separate
	from who (if anyone) it ends up linked to.
	"""
	url = f"{base_url}/gift_cards"
	payload = {
		"number": doc.certificate_code,
		# Sent as a raw JSON number, not a quoted string - str(doc.amount)
		# on a currency field like 35.0 also produced "35.0" (one decimal),
		# not "35.00", either of which could 400 against Lightspeed.
		"amount": round(float(doc.amount), 2),
		# expires_at is intentionally omitted/left empty - the gift
		# certificate's own expiration is tracked in the ERP, not mirrored
		# as a Lightspeed gift card expiry. time_zone/user_id are likewise
		# left out.
	}

	data = make_post_request(url, json=payload, headers=headers)
	gift_card = _unwrap_lightspeed_object(data)

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
	url = f"{base_url}/customers"
	response = make_get_request(url, params={"email": email}, headers=headers)
	response = response if isinstance(response, dict) else {}
	customers = response.get("data") or []
	return customers[0] if customers else None


def _create_lightspeed_customer(base_url, headers, doc):
	"""Create a new Lightspeed customer from the redeemer's details."""
	url = f"{base_url}/customers"
	payload = {
		"first_name": doc.first_name,
		"last_name": doc.last_name,
		"email": doc.email,
		"phone": doc.phone_number,
	}
	response = make_post_request(url, json=payload, headers=headers)
	customer = _unwrap_lightspeed_object(response)
	if not customer.get("id"):
		frappe.throw(_("Lightspeed did not return a customer ID after creation."))
	return customer


def _link_lightspeed_customer(base_url, headers, doc, context):
	"""
	Call 2 of 2: find or create the redeemer's Lightspeed customer, and
	record the link on their ERPNext Customer record (custom_lightspeed_id /
	lightspeed_customer_code) so this and future redemptions reuse the same
	Lightspeed customer instead of creating duplicates. A confirmed link is
	what "Linked" means for this certificate.

	Records each decision/result into `context` as it goes, so that if a
	later step throws, the error log already shows how far this got and
	with which Lightspeed customer - enough for staff to finish the
	redemption manually in Lightspeed without having to guess or redo work.
	"""
	customer_doc = frappe.get_doc("Customer", doc.redeemed_by)
	context["erpnext_customer"] = customer_doc.name

	if customer_doc.get("custom_lightspeed_id"):
		context["lightspeed_customer_lookup"] = "already linked on Customer record"
	else:
		found = _find_lightspeed_customer(base_url, headers, doc.email)
		context["lightspeed_customer_search_by_email"] = doc.email
		if found:
			context["lightspeed_customer_lookup"] = "found existing customer in Lightspeed"
			lightspeed_customer = found
		else:
			context["lightspeed_customer_lookup"] = "no match in Lightspeed - creating new customer"
			lightspeed_customer = _create_lightspeed_customer(base_url, headers, doc)

		context["lightspeed_customer_response"] = lightspeed_customer

		customer_doc.db_set("custom_lightspeed_id", lightspeed_customer.get("id"), commit=True)
		customer_doc.db_set(
			"lightspeed_customer_code", lightspeed_customer.get("customer_code"), commit=True
		)

	context["lightspeed_customer_id"] = customer_doc.get("custom_lightspeed_id")
	context["lightspeed_customer_code"] = customer_doc.get("lightspeed_customer_code")

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
	"""
	Returns True if the Lightspeed gift card itself was successfully
	created - this is "activation", the only part of this process the
	customer-facing redemption page reports on. Returns False if that step
	failed, so the customer can be told to reach out for help rather than
	being shown a false success.

	Linking the redeemer to a Lightspeed customer happens right after, but
	is purely internal bookkeeping (see the Gift Certificate's own
	Created/Activated/Linked status field). Any failure there is caught,
	logged with full context for staff to finish manually, and never
	changes the return value - the card itself still exists and is usable.
	"""
	# Filled in as each step below completes, so that if something fails
	# partway through, the error log shows exactly what already happened in
	# Lightspeed (and with which IDs) instead of just a traceback - enough
	# for staff to tell what's left to finish by hand.
	context = {
		"certificate_code": doc.certificate_code,
		"amount": doc.amount,
		"redeemer": f"{doc.first_name} {doc.last_name} <{doc.email}>",
		"erpnext_customer": doc.redeemed_by,
	}

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

		# Gift card creation needs its own scope (gift_cards:write:issue),
		# which the general "Lightspeed" key may not carry - use a
		# dedicated "Giftcards" row in Custom API Settings when one's
		# configured, falling back to the general "Lightspeed" credentials
		# otherwise so sites without a separate key keep working.
		gift_card_token, gift_card_base_url = get_provider_credentials("Giftcards")
		if not gift_card_token or not gift_card_base_url:
			gift_card_token, gift_card_base_url = token, base_url
		gift_card_headers = {
			"Authorization": f"Bearer {gift_card_token}",
			"Content-Type": "application/json",
			"Accept": "application/json",
		}

		if doc.status in ("Activated", "Linked"):
			# This is a retry after the customer-link step failed on an
			# earlier attempt (status="Activated" doesn't block
			# re-redemption - only Linked/Cancelled/Suspended/Expired do).
			# The gift card already exists in Lightspeed; recreating it
			# would send a duplicate `number` and likely get rejected,
			# wrongly telling an already-activated customer their card
			# failed. Skip straight to (re)trying the customer link.
			gift_card = {}
			context["gift_card_response"] = "skipped - already Activated in an earlier attempt"
		else:
			gift_card = _create_lightspeed_gift_card(gift_card_base_url, gift_card_headers, doc)
			context["gift_card_response"] = gift_card
			_console_log(f"Gift card created for {doc.certificate_code}", gift_card)
			doc.db_set("status", "Activated", commit=True)

	except Exception as e:
		context["error"] = str(e)
		_console_log(f"Activation FAILED for {doc.certificate_code}", context)
		frappe.log_error(
			title="Lightspeed gift card activation failed",
			message=_(
				"Could not activate gift certificate {0} in Lightspeed - the customer needs to be\n"
				"told to reach out, and this needs to be finished manually.\n\n{1}\n\nError: {2}\n\n{3}"
			).format(doc.certificate_code, frappe.as_json(context, indent=2), e, frappe.get_traceback()),
		)
		return False

	# From this point on, the gift card exists and the customer's
	# redemption succeeded - everything below is internal bookkeeping
	# (linking the Lightspeed customer, mirroring the Gift Card record) and
	# must never turn a successful activation into a customer-facing
	# failure. Any problem here is only ever logged for staff follow-up.
	try:
		customer_doc = _link_lightspeed_customer(base_url, headers, doc, context)
		_console_log(f"Customer linked for {doc.certificate_code}", context)
		doc.db_set("status", "Linked", commit=True)

		_upsert_gift_card(doc, gift_card, customer_doc)

		frappe.msgprint(
			_("Gift Card <b>{0}</b> successfully created in Lightspeed (Balance: {1}, Customer ID: {2})").format(
				doc.certificate_code, gift_card.get("balance", doc.amount), context.get("lightspeed_customer_id")
			),
			indicator="green",
			alert=True,
		)

	except Exception as e:
		context["error"] = str(e)
		_console_log(f"Customer link FAILED for {doc.certificate_code} (gift card was created OK)", context)
		frappe.log_error(
			title="Lightspeed customer link failed - finish manually",
			message=_(
				"Gift card {0} was created successfully in Lightspeed, but linking the redeemer's\n"
				"Lightspeed customer failed. The customer was NOT told about this - the gift card is\n"
				"usable. Use this to link the customer manually in Lightspeed:\n\n{1}\n\nError: {2}\n\n{3}"
			).format(doc.certificate_code, frappe.as_json(context, indent=2), e, frappe.get_traceback()),
		)
		frappe.msgprint(
			_("Gift Card <b>{0}</b> created in Lightspeed, but linking the customer failed - see Error Log.").format(
				doc.certificate_code
			),
			indicator="orange",
			alert=True,
		)

	return True


# Register new providers here as they come online, e.g. "Square": _activate_square
PROVIDER_HANDLERS = {
	"Lightspeed": _activate_lightspeed,
}
