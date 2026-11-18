"""Score extraction and end-to-end risk vs gold. Usage: python eval.py --mode baseline|llm"""
import argparse, json
from analyze import baseline, llm_extract, ground, risk

def run(mode):
    crs = json.load(open("data/change_requests.json")); tp = fp = fn = rej_total = 0
    rb_ok = te_ok = risk_ok = hi_tp = hi_fn = hi_fp = silent = flagged = 0; imp = [0, 0]; exp = [0, 0]; wrong = []
    for c in crs:
        facts, rej = ground(baseline(c["text"]) if mode == "baseline" else llm_extract(c["text"]), c["text"]); rej_total += len(rej)
        got = {x["name"] for x in facts["components"]}; gold = set(c["components"])
        tp += len(got & gold); fp += len(got - gold); fn += len(gold - got)
        bucket = imp if c["implicit"] else exp; bucket[1] += len(gold); bucket[0] += len(got & gold)
        rb_ok += facts["has_rollback_plan"] == c["rollback"]; te_ok += facts["has_test_evidence"] == c["testing"]
        g = risk(c["components"], c["rollback"], c["testing"]); p = risk(sorted(got), facts["has_rollback_plan"], facts["has_test_evidence"])
        risk_ok += g == p; hi_tp += g == p == "High"; hi_fn += g == "High" and p != "High"; flagged += p == "Needs review"; silent += g == "High" and p not in ("High", "Needs review"); hi_fp += p == "High" and g != "High"
        if g != p or got != gold: wrong.append((c["id"], f"comps {sorted(got)} vs {sorted(gold)}" if got != gold else "", f"risk {p} vs {g}" if g != p else ""))
    n = len(crs); P = tp / (tp + fp) if tp + fp else 0; R = tp / (tp + fn) if tp + fn else 0
    print(f"mode={mode} n={n}  component precision={P:.2f} recall={R:.2f}  (ungrounded rejected={rej_total})")
    print(f"recall on explicitly named systems={exp[0]}/{exp[1]}  on indirectly referenced systems={imp[0]}/{imp[1]}")
    print(f"rollback-flag accuracy={rb_ok}/{n}  test-flag accuracy={te_ok}/{n}")
    print(f"end-to-end risk level accuracy={risk_ok}/{n} ({risk_ok/n:.0%})  High-risk recall={hi_tp}/{hi_tp+hi_fn}  High-risk false alarms={hi_fp}")
    print(f"flagged for human review (nothing identified)={flagged}  HIGH-risk changes missed SILENTLY (rated lower, not flagged)={silent}")
    for w in wrong: print("  miss", *w)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--mode", choices=["baseline", "llm"], default="baseline"); run(ap.parse_args().mode)

# Created by Avash Mohanty, 2026
