"""17 synthetic change requests with hand-assigned gold facts. Small, author-labelled: illustration, not a benchmark.
(text, gold_components, has_rollback, has_test_evidence, implicit_component_reference)"""
import json
CR = [
("Upgrade the SSO Gateway TLS library to 3.2. Tested in staging with full login regression. Rollback: redeploy previous container image.", ["SSO Gateway"], True, True, False),
("Patch the nightly jobs runner to fix the timezone bug. Deploy Sunday 02:00. No rollback plan yet, to be defined.", ["Batch Scheduler"], False, False, False),
("Change invoice rounding logic in the invoicing service. Unit tests pass. Rollback via feature flag.", ["Billing API"], True, True, False),
("Increase the connection pool on the customer database. Applied in production during business hours. No testing done.", ["Customer DB"], False, False, False),
("Extend audit log retention config from 90 to 365 days. Tested in dev. Revert by restoring the config.", ["Audit Log Service"], True, True, False),
("Move the email service to a new SMTP relay. Smoke test in staging passed. Rollback: switch the relay back via DNS.", ["Notification Service"], True, True, False),
("Replace the card processing endpoint URLs and rotate keys. Tested with sandbox transactions. No rollback documented.", ["Payments Gateway"], False, True, False),
("Add a department attribute to the user directory schema and adjust the single sign-on claims mapping to include it. Tested end to end in UAT. Rollback: restore schema snapshot.", ["Identity Directory", "SSO Gateway"], True, True, False),
("Add a region column to the data warehouse fact table. Regression tested in the test environment; rollback script attached.", ["Reporting DWH"], True, True, False),
("Hotfix for the back-office portal permissions screen. Rolled out straight to production, we will watch the logs.", ["Admin Portal"], False, False, False),
("Decommission the old file store bucket after migrating contracts. Migration verified by checksum. Rollback: bucket retained for 30 days.", ["Document Store"], True, True, False),
("Change how the thing that sends customers their receipts batches messages, from 100 to 500 per run. Tested in staging, can be reverted by config.", ["Notification Service"], True, True, True),
("Rewrite the customer lookup queries in the CRM database for performance. Staging benchmark attached. Rollback plan: keep the old indexes.", ["Customer DB"], True, True, False),
("Update the iOS app login flow to use the new token format; the login service must accept the new token too. Tested on devices. Rollback: previous app version stays available.", ["Mobile App", "SSO Gateway"], True, True, False),
("Shift the end-of-day processing window from 23:00 to 22:00 so overnight reconciliation finishes earlier. Confirmed with operations, test run in staging, can revert the schedule.", ["Batch Scheduler"], True, True, True),
("Rotate service credentials for everything that talks to payments and customer records, during the weekend. Tested rotation in staging. Rollback: previous credentials valid for 24h.", ["Payments Gateway", "Customer DB"], True, True, True),
("Switch the login page to the new brand theme. Visual check done. No functional change.", ["SSO Gateway"], False, True, False),
]
json.dump([{"id": f"CR-{i:02d}", "text": t, "components": c, "rollback": r, "testing": e, "implicit": im} for i, (t, c, r, e, im) in enumerate(CR, 1)],
          open("data/change_requests.json", "w"), indent=1)
print(len(CR), "change requests")

# Created by Avash Mohanty, 2026
