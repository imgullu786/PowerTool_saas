import boto3
import frappe
from botocore.exceptions import ClientError
from frappe import _
from frappe.utils.password import get_decrypted_password


def _get_settings():
	return frappe.get_single("PT SaaS Settings")


def _get_secret_key() -> str | None:
	return get_decrypted_password(
		"PT SaaS Settings",
		"PT SaaS Settings",
		"aws_secret_access_key",
		raise_exception=False,
	)


def get_s3_client():
	settings = _get_settings()
	access_key = settings.aws_access_key_id
	secret_key = _get_secret_key()
	region = settings.aws_region

	if not region:
		frappe.throw(_("AWS Region not configured."))
	if not access_key:
		frappe.throw(_("AWS Access Key ID not configured."))
	if not secret_key:
		frappe.throw(_("AWS Secret Access Key not found."))
	return boto3.client(
		"s3",
		aws_access_key_id=access_key,
		aws_secret_access_key=secret_key,
		region_name=region,
	)


def get_bucket_name() -> str:
	settings = _get_settings()
	if not settings.aws_bucket:
		frappe.throw(_("S3 Bucket Name not configured."))
	return settings.aws_bucket


def generate_presigned_put(object_key: str, expiration: int = 3600) -> str | None:
	try:
		return get_s3_client().generate_presigned_url(
			"put_object",
			Params={"Bucket": get_bucket_name(), "Key": object_key},
			ExpiresIn=expiration,
		)
	except ClientError as e:
		frappe.log_error("S3 Presigned PUT Error", str(e))
		return None


def generate_presigned_get(object_key: str, expiration: int = 3600) -> str | None:
	try:
		return get_s3_client().generate_presigned_url(
			"get_object",
			Params={"Bucket": get_bucket_name(), "Key": object_key},
			ExpiresIn=expiration,
		)
	except ClientError as e:
		frappe.log_error("S3 Presigned GET Error", str(e))
		return None
