"""Change request -> impacted components, blast radius, risk level, missing controls.

Design principle: the LLM only turns unstructured text into structured facts (which catalogued systems, is there a rollback
plan, is there test evidence). Blast radius and risk are computed by deterministic code from the catalog graph, so the part
that must be auditable is never left to a model.
"""
import json, re
from llm import complete, parse_json

CATALOG = {s["name"]: s for s in json.load(open("data/catalog.json"))["systems"]}
LEVELS = ["Low", "Medium", "High"]

def dependents(changed):
    """Transitive set of systems that consume any changed system (excluding the changed ones)."""
    out, frontier = set(), set(changed)
    while frontier:
        nxt = {n for n, s in CATALOG.items() if set(s["depends_on"]) & frontier} - out - set(changed)
        out |= nxt; frontier = nxt
    return out

def risk(changed, rollback, testing):
    if not changed:
        return "Needs review"  # never report Low just because nothing was identified
    lvl = 0
    crits = [CATALOG[c]["criticality"] for c in changed]
    if "high" in crits: lvl = 2
    elif "medium" in crits: lvl = 1
    blast = len(dependents(changed))
    if blast >= 4: lvl = max(lvl, 2)
    elif blast >= 2: lvl = max(lvl, 1)
    if not rollback or not testing: lvl = min(2, lvl + 1)
    return LEVELS[lvl]

# ---------- baseline: alias matching + keyword flags ----------
def baseline(text):
    t = text.lower()
    comps = [n for n, s in CATALOG.items() if any(a in t for a in [n.lower()] + s["aliases"])]
    rb = bool(re.search(r"rollback|roll back|revert|restore|retained|switch .*back|previous", t)) and not re.search(r"no rollback|without rollback", t)
    te = bool(re.search(r"tested|test run|regression|benchmark|smoke|verified|visual check|unit tests", t)) and not re.search(r"no testing|not tested", t)
    return {"components": [{"name": c, "evidence": ""} for c in comps], "has_rollback_plan": rb, "has_test_evidence": te}

# ---------- LLM ----------
def system_prompt():
    cat = "\n".join(f"- {n}: also called {', '.join(s['aliases'])}" for n, s in CATALOG.items())
    return f"""You read an IT change request and extract facts. Return ONLY JSON:
{{"components":[{{"name":"<exact catalog name>","evidence":"<EXACT verbatim phrase from the change request that refers to it>"}}],"has_rollback_plan":true|false,"has_test_evidence":true|false}}
Catalog (use these exact names only; never invent a system):
{cat}
Rules: list only systems the change itself modifies, not systems merely mentioned as context. Include systems referred to indirectly
(e.g. "the thing that sends receipts") if the catalog clearly matches. has_rollback_plan is true only if a concrete way back is stated.
has_test_evidence is true only if testing actually done is stated (not planned). Never guess; if unsure whether a system is affected, leave it out."""

def llm_extract(text):
    return parse_json(complete(system_prompt(), "Change request:\n" + text, max_tokens=600))

def ground(facts, text):
    """Keep only components that exist in the catalog AND whose evidence phrase appears in the request."""
    norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()
    kept, rejected = [], []
    for c in facts.get("components", []):
        ok = c.get("name") in CATALOG and (c.get("evidence") == "" or norm(c.get("evidence", "")) in norm(text))
        (kept if ok and c["name"] not in [k["name"] for k in kept] else rejected).append(c)
    return {**facts, "components": kept}, rejected

def report(cr_id, text, facts):
    names = [c["name"] for c in facts["components"]]
    imp = sorted(dependents(names)); lvl = risk(names, facts["has_rollback_plan"], facts["has_test_evidence"])
    gaps = [g for ok, g in [(facts["has_rollback_plan"], "no concrete rollback plan"), (facts["has_test_evidence"], "no test evidence")] if not ok]
    lvl = "UNKNOWN, no catalogued system identified: human review required" if lvl == "Needs review" else lvl
    return (f"# Change impact: {cr_id}\n\n**Risk: {lvl}**\n\n- Directly changed: {', '.join(names) or 'none identified (needs human review)'}\n"
            f"- Downstream blast radius ({len(imp)}): {', '.join(imp) or 'none'}\n- Missing controls: {', '.join(gaps) or 'none'}\n\n"
            "_AI-assisted draft. The CAB/change owner confirms components and risk before approval._\n")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", choices=["baseline", "llm"], default="baseline"); ap.add_argument("--cr", default="CR-04")
    a = ap.parse_args(); cr = next(c for c in json.load(open("data/change_requests.json")) if c["id"] == a.cr)
    facts, rej = ground(baseline(cr["text"]) if a.mode == "baseline" else llm_extract(cr["text"]), cr["text"])
    md = report(cr["id"], cr["text"], facts); open("output/sample_report.md", "w").write(md); print(md); print(f"[rejected ungrounded components: {len(rej)}]")

# Created by Avash Mohanty, 2026
