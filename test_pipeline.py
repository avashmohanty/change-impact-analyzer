"""Offline tests with a faked LLM: blast-radius graph, risk rules, grounding of hallucinated systems/quotes."""
import analyze
from analyze import dependents, risk, ground

assert dependents(["Customer DB"]) == {"Billing API", "Batch Scheduler", "Reporting DWH", "Admin Portal", "Mobile App"}, dependents(["Customer DB"])
assert dependents(["Document Store"]) == set()
assert dependents(["Identity Directory"]) == {"SSO Gateway", "Admin Portal", "Mobile App"}
assert risk(["Document Store"], True, True) == "Low" and risk(["Document Store"], False, True) == "Medium"
assert risk([], True, True) == "Needs review"
assert risk(["Customer DB"], True, True) == "High" and risk(["Audit Log Service"], True, True) == "Medium"

text = "Tune the customer database pool. Tested in staging. Rollback: revert config."
analyze.complete = lambda *a, **k: ('Result:\n```json\n{"components":[{"name":"Customer DB","evidence":"customer database pool"},'
    '{"name":"Quantum Router","evidence":"customer database pool"},{"name":"Billing API","evidence":"the billing cluster"}],'
    '"has_rollback_plan":true,"has_test_evidence":true}\n```')
facts, rejected = ground(analyze.llm_extract(text), text)
assert [c["name"] for c in facts["components"]] == ["Customer DB"] and len(rejected) == 2
print("PASS: graph blast radius, risk rules, hallucinated system and hallucinated quote both rejected")

# Created by Avash Mohanty, 2026
