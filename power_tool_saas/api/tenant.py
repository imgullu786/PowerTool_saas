import hashlib
import secrets

import frappe
from frappe import _


def _hash_key(plain_key: str) -> str:
	return hashlib.sha256(plain_key.encode()).hexdigest()


def _get_tenant_for_user(user: str) -> str | None:
	"""Return the Tenant name owned by this user, or None."""
	return frappe.db.get_value("PT Tenant", {"tenant": user}, "name")


@frappe.whitelist(allow_guest=True)
def signup(email: str, company_name: str, first_name: str, last_name: str, password: str):
	from frappe.utils.password import update_password

	email = email.strip().lower()

	if frappe.db.exists("User", email):
		frappe.throw(_("An account with this email already exists."))

	if frappe.db.exists("PT Tenant", {"tenant": email}):
		frappe.throw(_("A tenant account already exists for this email."))

	# Create Frappe User
	user_doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": email,
			"first_name": first_name,
			"last_name": last_name,
			"send_welcome_email": 0,
			"user_type": "Website User",
		}
	)
	user_doc.insert(ignore_permissions=True)

	update_password(user_doc.name, password)

	# Create linked PT Tenant
	tenant_doc = frappe.get_doc(
		{
			"doctype": "PT Tenant",
			"tenant": email,
			"organisation_name": company_name.strip(),
		}
	)
	tenant_doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"tenant": tenant_doc.name,
		"user": email,
	}


@frappe.whitelist()
def register_site(site_url: str):
	user = frappe.session.user

	if user == "Guest":
		frappe.throw(_("You must be logged in to register a site."), frappe.AuthenticationError)

	# Find this user's tenant
	tenant = _get_tenant_for_user(user)
	if not tenant:
		frappe.throw(
			_("No Tenant account found for your user. Please contact support to get your account set up.")
		)

	# Check for duplicate site URLs of same tenant
	if frappe.db.exists("PT Tenant Site", {"tenant": tenant, "site_url": site_url}):
		frappe.throw(_("A site with URL {0} is already registered under your account.").format(site_url))

	plain_key = secrets.token_hex(32)

	site_doc = frappe.new_doc("PT Tenant Site")
	site_doc.tenant = tenant
	site_doc.site_url = site_url
	site_doc.api_hash_key = _hash_key(plain_key)
	site_doc.used_storage_bytes = 0
	site_doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"tenant_site": site_doc.name,
		"site_url": site_url,
		"api_key": plain_key,
	}


@frappe.whitelist()
def regenerate_api_key(tenant_site: str):
	user = frappe.session.user

	if user == "Guest":
		frappe.throw(_("You must be logged in."), frappe.AuthenticationError)

	# Verify the site belongs to this user
	tenant = _get_tenant_for_user(user)
	site_tenant = frappe.db.get_value("PT Tenant Site", tenant_site, "tenant")

	if not tenant or site_tenant != tenant:
		frappe.throw(_("Not authorized for this site."), frappe.PermissionError)

	plain_key = secrets.token_hex(32)
	frappe.db.set_value("PT Tenant Site", tenant_site, "api_hash_key", _hash_key(plain_key))
	frappe.db.commit()

	return {"tenant_site": tenant_site, "api_key": plain_key}


@frappe.whitelist()
def get_sites():
	user = frappe.session.user

	if user == "Guest":
		frappe.throw(_("You must be logged in."), frappe.AuthenticationError)

	tenant = _get_tenant_for_user(user)
	if not tenant:
		return []

	return frappe.get_all(
		"PT Tenant Site",
		filters={"tenant": tenant},
		fields=["name", "site_url", "used_storage_bytes", "creation"],
		order_by="creation desc",
		ignore_permissions=True,
	)
