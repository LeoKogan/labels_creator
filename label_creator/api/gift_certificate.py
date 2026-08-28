import frappe
from frappe import _
from frappe.utils import formatdate, getdate, nowdate, validate_email_address

from label_creator.utils.gift_certificate_providers import activate_gift_certificate

def _not_redeemable_message(status):
	return {
		"Cancelled": _("This gift certificate has been cancelled."),
		"Suspended": _("This gift certificate is currently suspended. Please contact us for help."),
		"Linked": _("This gift certificate has already been redeemed."),
		"Expired": _("This gift certificate has expired."),
	}.get(status)


@frappe.whitelist(allow_guest=True)
def register_gift_certificate(action=None, certificate_code=None, first_name=None,
	last_name=None, email=None, phone_number=None):
	"""
	Public endpoint backing the /gift-certificate-redeem web page.

	action="validate": confirm the code exists and is redeemable, and return
	the Gift Certificate Type's logo for branding.
	action="register": capture the redeemer's details and mark the
	certificate as Linked.
	"""
	certificate_code = (certificate_code or "").strip()
	if not certificate_code:
		frappe.throw(_("Certificate code is required."))

	gift_certificate = frappe.db.get_value(
		"Gift Certificate",
		certificate_code,
		["name", "status", "expiration", "amount", "gift_certificate_type"],
		as_dict=True,
	)
	if not gift_certificate:
		frappe.throw(_("We couldn't find a gift certificate with that code."))

	if action == "validate":
		return _validate(gift_certificate)
	elif action == "register":
		return _register(gift_certificate, first_name, last_name, email, phone_number)

	frappe.throw(_("Invalid action."))


def _validate(gift_certificate):
	_ensure_redeemable(gift_certificate)

	app_logo = None
	if gift_certificate.gift_certificate_type:
		app_logo = frappe.db.get_value(
			"Gift Certificate Type", gift_certificate.gift_certificate_type, "logo_url"
		)

	return {"status": "success", "app_logo": app_logo}


def _register(gift_certificate, first_name, last_name, email, phone_number):
	_ensure_redeemable(gift_certificate)

	missing = [
		label
		for label, value in (
			(_("First Name"), first_name),
			(_("Last Name"), last_name),
			(_("Email"), email),
			(_("Phone Number"), phone_number),
		)
		if not value
	]
	if missing:
		frappe.throw(_("Please fill in: {0}").format(", ".join(missing)))

	validate_email_address(email, throw=True)

	customer = _get_or_create_customer(first_name, last_name, email, phone_number)

	doc = frappe.get_doc("Gift Certificate", gift_certificate.name)
	doc.first_name = first_name
	doc.last_name = last_name
	doc.email = email
	doc.phone_number = phone_number
	doc.redeem_date = nowdate()
	doc.redeemed_by = customer
	doc.status = "Linked"
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	# Create the matching POS gift card (e.g. Lightspeed) now that the
	# certificate is actually being redeemed, not when it was first created.
	activate_gift_certificate(doc)

	return {
		"status": "success",
		"message": _("Your gift certificate has been activated. Thank you, {0}!").format(first_name),
	}


def _ensure_redeemable(gift_certificate):
	message = _not_redeemable_message(gift_certificate.status)
	if message:
		frappe.throw(message)

	if gift_certificate.expiration and getdate(gift_certificate.expiration) < getdate(nowdate()):
		frappe.throw(
			_("This gift certificate expired on {0}.").format(formatdate(gift_certificate.expiration))
		)


def _get_or_create_customer(first_name, last_name, email, phone_number):
	existing = frappe.db.get_value("Customer", {"email_id": email}, "name")
	if existing:
		return existing

	customer = frappe.get_doc({
		"doctype": "Customer",
		"customer_name": f"{first_name} {last_name}".strip(),
		"customer_type": "Individual",
		"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "All Customer Groups",
		"territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories",
		"email_id": email,
		"mobile_no": phone_number,
	})
	customer.insert(ignore_permissions=True)
	return customer.name
