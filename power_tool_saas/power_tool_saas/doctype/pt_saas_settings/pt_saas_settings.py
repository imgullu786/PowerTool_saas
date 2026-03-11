# Copyright (c) 2026, Md Gulam Gaush and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password


class PTSaaSSettings(Document):
	def validate(self):
		if self.aws_access_key_id:
			self.aws_access_key_id = self.aws_access_key_id.strip()
		if self.aws_region:
			self.aws_region = self.aws_region.strip()
		if self.aws_bucket:
			self.aws_bucket = self.aws_bucket.strip()


def _get_aws_secret_key() -> str | None:
	return get_decrypted_password(
		"PT SaaS Settings",
		"PT SaaS Settings",
		"aws_secret_access_key",
		raise_exception=False,
	)


@frappe.whitelist()
def test_s3_connection():
	import boto3
	from botocore.exceptions import ClientError, EndpointConnectionError, NoCredentialsError

	settings = frappe.get_single("PT SaaS Settings")
	secret_key = _get_aws_secret_key()
	if not secret_key:
		frappe.throw(_("AWS Secret Access Key could not be decrypted."))

	try:
		client = boto3.client(
			"s3",
			aws_access_key_id=settings.aws_access_key_id,
			aws_secret_access_key=secret_key,
			region_name=settings.aws_region,
		)
		client.head_bucket(Bucket=settings.aws_bucket)
		frappe.db.set_value("PT SaaS Settings", None, "connection_status", "Connected")
		frappe.db.commit()
		return {"status": "Connected"}

	except (ClientError, NoCredentialsError, EndpointConnectionError) as e:
		frappe.db.set_value("PT SaaS Settings", None, "connection_status", "Error")
		frappe.db.commit()
		return {"status": "Error", "message": str(e)}
