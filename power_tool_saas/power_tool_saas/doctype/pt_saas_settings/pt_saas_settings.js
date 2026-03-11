// Copyright (c) 2026, Md Gulam Gaush and contributors
// For license information, please see license.txt

frappe.ui.form.on("PT SaaS Settings", {
	refresh(frm) {
		// Only show the test button when the form is saved (not dirty)
		if (frm.is_dirty()) return;

		frm.add_custom_button(__("Test S3 Connection"), () => {
			frappe.show_alert({ message: __("Testing connection..."), indicator: "blue" });

			frappe.call({
				method: "power_tool_saas.power_tool_saas.doctype.pt_saas_settings.pt_saas_settings.test_s3_connection",
				callback(r) {
					if (r.message && r.message.status === "Connected") {
						frappe.show_alert({ message: __("S3 Connected ✅"), indicator: "green" });
					} else {
						frappe.show_alert({
							message:
								__("Connection Failed: ") +
								(r.message?.message || "Unknown error"),
							indicator: "red",
						});
					}
					frm.reload_doc();
				},
			});
		});
	},
});
