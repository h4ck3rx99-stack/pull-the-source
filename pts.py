#!/usr/bin/env python3
"""PULL THE SOURCE -- prompt building, response ingestion, scoring.

  python3 pts.py prepare-initial  --set eval|practice
  python3 pts.py prepare-branches --set eval|practice   (needs initial responses)
  python3 pts.py ingest           --set eval|practice   (responses/*.txt -> log.jsonl)
  python3 pts.py score            --set eval|practice
  python3 pts.py selfcheck
  python3 pts.py freeze

A "call" = one prompt file in runs/<set>/prompts/<call_id>.txt answered by one
fresh model context that writes runs/<set>/responses/<call_id>.txt.
Answer keys are only read by `score`/`selfcheck`, never by prompt building.
"""
import json, os, re, sys, hashlib, argparse, datetime, math
HERE = os.path.dirname(os.path.abspath(__file__))
CONDS = ["A", "B"]
LABELS = ["Supported", "Contradicted", "Insufficient evidence"]

RULES = """You are helping with a purchase decision in a fictional scenario. Decide whether the recommendation below is justified solely by the currently valid supplied sources.

Rules
1. Use only the supplied sources. Do not use outside knowledge or assumptions about the product.
2. A requirement counts as established only if a currently valid source establishes it for the exact product named in the recommendation, either by stating it directly or by giving a specific measurement, rating or test result that meets the stated threshold by simple comparison. Vague descriptions and sources about other products or models do not establish a requirement.
3. Choose exactly one label:
   - Supported: every requirement is established by currently valid sources.
   - Contradicted: a currently valid source explicitly shows that a requirement is not met.
   - Insufficient evidence: neither of the above.
4. A source may later be withdrawn. A withdrawn source is no longer usable as evidence. Withdrawal does not show that what the source said is false.
5. "Insufficient evidence" is always a permitted answer.
"""
FORMAT_COMMON = """Give a brief justification, then end with exactly these two lines:
RELIES_ON: <comma-separated IDs of the sources your decision depends on, or NONE>
DECISION: <Supported | Contradicted | Insufficient evidence>"""
FORMAT = {
 "A": "Output format\n" + FORMAT_COMMON,
 "B": "Output format\nFirst write a dependency table with one row per requirement and these columns: Requirement | Source IDs it depends on | Is each of those sources currently valid?\nThen decide. " + FORMAT_COMMON,
}
FOLLOWUP = {
 "A": "Update: source {sid} has been withdrawn and is no longer valid. All other sources are unchanged. Apply the same rules and give your current decision in the same output format.",
 "B": "Update: source {sid} has been withdrawn and is no longer valid. All other sources are unchanged. Apply the same rules. Update your dependency table first, then give your current decision in the same output format.",
}
REPLAY = """Below is a conversation so far between a USER and you (the ASSISTANT). Write only the ASSISTANT's next reply.

----- USER -----
{initial_prompt}

----- ASSISTANT -----
{initial_response}

----- USER -----
{followup}
"""

def initial_prompt(sc, cond):
    reqs = "\n".join(f"{r['id']}. {r['text']}" for r in sc["requirements"])
    srcs = "\n".join(f"{s['id']}. {s['text']}" for s in sc["sources"])
    return (f"{RULES}\nRecommendation: \"{sc['recommendation']}\"\n\n{sc['buyer']}'s requirements\n{reqs}\n\n"
            f"Sources (all currently valid)\n{srcs}\n\n{FORMAT[cond]}\n")

def paths(setname):
    base = f"{HERE}/runs/{setname}"
    for d in ("prompts", "responses"): os.makedirs(f"{base}/{d}", exist_ok=True)
    return base
def load(setname): return json.load(open(f"{HERE}/data/{setname}_scenarios.json"))
def load_keys(setname): return {k["id"]: k for k in json.load(open(f"{HERE}/keys/{setname}_keys.json"))}
def rd(p): return open(p, encoding="utf-8").read() if os.path.exists(p) else None

def prepare_initial(setname):
    base = paths(setname); n = 0
    for sc in load(setname):
        for c in CONDS:
            open(f"{base}/prompts/{sc['id']}_{c}_init.txt", "w").write(initial_prompt(sc, c)); n += 1
    print("wrote", n, "initial prompts")

def prepare_branches(setname):
    base = paths(setname); n = 0; missing = []
    for sc in load(setname):
        for c in CONDS:
            resp = rd(f"{base}/responses/{sc['id']}_{c}_init.txt")
            if resp is None: missing.append(f"{sc['id']}_{c}_init"); continue
            for b in sc["branches"]:
                txt = REPLAY.format(initial_prompt=initial_prompt(sc, c).strip(), initial_response=resp.strip(),
                                    followup=FOLLOWUP[c].format(sid=b["withdraw"]))
                open(f"{base}/prompts/{sc['id']}_{c}_br{b['branch']}.txt", "w").write(txt); n += 1
    print("wrote", n, "branch prompts; missing initial responses:", missing)

def parse(resp):
    """Deterministic parser. Returns (decision or 'UNPARSED', relies_on list or None)."""
    if resp is None: return "MISSING", None
    clean = resp.replace("*", "").replace("`", "")
    m = re.findall(r"DECISION\s*:\s*(.+)", clean)
    dec = "UNPARSED"
    if m:
        v = m[-1].strip().lower()
        for L in LABELS:
            if v.startswith(L.lower()): dec = L
    m = re.findall(r"RELIES_ON\s*:\s*(.+)", clean)
    rel = sorted(set(re.findall(r"S\d+", m[-1]))) if m else None
    return dec, rel

def ingest(setname, model="claude-haiku (Agent-tool alias 'haiku'; exact ID not exposed)", settings="agent harness defaults; temperature not controllable"):
    base = paths(setname); rows = []
    for fn in sorted(os.listdir(f"{base}/prompts")):
        cid = fn[:-4]; sid, cond, stage = cid.split("_")
        rp = f"{base}/responses/{fn}"; resp = rd(rp)
        dec, rel = parse(resp)
        rows.append(dict(call_id=cid, set=setname, scenario=sid, condition=cond, stage=stage,
                         model=model, settings=settings,
                         prompt=rd(f"{base}/prompts/{fn}"), response=resp,
                         response_written_utc=(datetime.datetime.fromtimestamp(os.path.getmtime(rp), datetime.timezone.utc).isoformat(timespec="seconds") if resp is not None else None),
                         error=(None if resp is not None else "no response file"),
                         parsed_decision=dec, parsed_relies_on=rel))
    with open(f"{base}/log.jsonl", "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    bad = [r["call_id"] for r in rows if r["parsed_decision"] in ("MISSING", "UNPARSED")]
    print(f"{setname}: {len(rows)} calls logged; missing/unparsed: {bad}")

def sign_test(b, c):
    n = b + c
    if n == 0: return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)

def score_rows(rows, scen, keys):
    """rows: list of dict(scenario, condition, stage, parsed_decision, parsed_relies_on)."""
    by = {(r["scenario"], r["condition"], r["stage"]): r for r in rows}
    out = {"conditions": {}, "per_call": []}
    std = [s for s in scen if keys[s["id"]]["kind"] == "standard"]
    for c in CONDS:
        def stats(subset):
            m = dict(n_scenarios=len(subset), essential_correct=0, essential_retained_supported=0, essential_other=0,
                     irrelevant_correct=0, irrelevant_unnecessary_withdrawal=0,
                     redundant_correct_retention=0, redundant_wrong=0, post_correct=0, post_total=0,
                     scenarios_all3_correct=0)
            for s in subset:
                k = keys[s["id"]]; ok = 0
                for b, kb in k["branches"].items():
                    d = by.get((s["id"], c, "br" + b), {}).get("parsed_decision", "MISSING")
                    good = d == kb["gold"]; ok += good; m["post_total"] += 1; m["post_correct"] += good
                    if kb["type"] == "essential":
                        m["essential_correct"] += good
                        m["essential_retained_supported"] += d == "Supported"
                        m["essential_other"] += (not good and d != "Supported")
                    elif kb["type"] == "irrelevant":
                        m["irrelevant_correct"] += good; m["irrelevant_unnecessary_withdrawal"] += not good
                    elif kb["type"] == "redundant":
                        m["redundant_correct_retention"] += good; m["redundant_wrong"] += not good
                m["scenarios_all3_correct"] += ok == len(k["branches"])
            return m
        init_ok = [s for s in std if by.get((s["id"], c, "init"), {}).get("parsed_decision") == keys[s["id"]]["initial_gold"]]
        out["conditions"][c] = dict(initial_correct=len(init_ok), initial_total=len(std),
                                    initial_wrong=[s["id"] for s in std if s not in init_ok],
                                    all_cases=stats(std), initially_correct_cases=stats(init_ok))
    # paired scenario-level comparison (branches within a scenario are related -> unit = scenario)
    def all3(s, c):
        k = keys[s["id"]]
        return all(by.get((s["id"], c, "br" + b), {}).get("parsed_decision") == kb["gold"] for b, kb in k["branches"].items())
    pa = dict(both=0, A_only=0, B_only=0, neither=0)
    for s in std:
        a, b = all3(s, "A"), all3(s, "B")
        pa["both" if a and b else "A_only" if a else "B_only" if b else "neither"] += 1
    pa["exact_sign_test_p_two_sided"] = sign_test(pa["A_only"], pa["B_only"])
    out["paired_scenario_level_all3_correct"] = pa
    # reference policies computed from the key (NOT model runs)
    ref = {}
    for name, f in [("always_insufficient", lambda g: "Insufficient evidence"), ("always_supported", lambda g: "Supported")]:
        ref[name] = dict(initial_correct=sum(f(0) == keys[s["id"]]["initial_gold"] for s in std), initial_total=len(std),
                         post_correct=sum(f(0) == kb["gold"] for s in std for kb in keys[s["id"]]["branches"].values()),
                         post_total=sum(len(keys[s["id"]]["branches"]) for s in std))
    out["reference_policies_not_model_runs"] = ref
    # exploratory: stated dependencies
    sec = {}
    for c in CONDS:
        t = dict(n=0, stated_equals_key_support_set=0, stated_includes_near_miss=0, stated_includes_irrelevant=0, stated_unparsed=0,
                 withdrawn_in_stated=dict(decision_changed=0, decision_kept=0),
                 withdrawn_not_in_stated=dict(decision_changed=0, decision_kept=0))
        for s in std:
            k = keys[s["id"]]; r0 = by.get((s["id"], c, "init"))
            if not r0: continue
            t["n"] += 1; rel = r0.get("parsed_relies_on")
            if rel is None: t["stated_unparsed"] += 1; continue
            sup = sorted(x for x, v in k["sources"].items() if v["supports"])
            t["stated_equals_key_support_set"] += rel == sup
            t["stated_includes_near_miss"] += any(k["sources"].get(x, {}).get("role") == "N" for x in rel)
            t["stated_includes_irrelevant"] += any(k["sources"].get(x, {}).get("role") == "I" for x in rel)
            for b, kb in k["branches"].items():
                rb = by.get((s["id"], c, "br" + b))
                if not rb or rb["parsed_decision"] in ("MISSING", "UNPARSED"): continue
                changed = rb["parsed_decision"] != r0["parsed_decision"]
                t["withdrawn_in_stated" if kb["withdraw"] in rel else "withdrawn_not_in_stated"]["decision_changed" if changed else "decision_kept"] += 1
        sec[c] = t
    out["exploratory_stated_dependencies"] = sec
    for s in scen:
        k = keys[s["id"]]
        for c in CONDS:
            for stage, gold, typ in [("init", k["initial_gold"], "initial")] + [("br" + b, kb["gold"], kb["type"]) for b, kb in k["branches"].items()]:
                r = by.get((s["id"], c, stage))
                d = r["parsed_decision"] if r else "MISSING"
                out["per_call"].append(dict(scenario=s["id"], condition=c, stage=stage, type=typ, gold=gold, decision=d, correct=d == gold))
    return out

def score(setname):
    base = paths(setname)
    rows = [json.loads(l) for l in open(f"{base}/log.jsonl")]
    res = score_rows(rows, load(setname), load_keys(setname))
    res["set"] = setname; res["n_calls_logged"] = len(rows)
    res["calls_missing_or_unparsed"] = [r["call_id"] for r in rows if r["parsed_decision"] in ("MISSING", "UNPARSED")]
    os.makedirs(f"{HERE}/results", exist_ok=True)
    json.dump(res, open(f"{HERE}/results/{setname}_scores.json", "w"), indent=1)
    for c in CONDS:
        x = res["conditions"][c]; a = x["all_cases"]; i = x["initially_correct_cases"]
        print(f"[{setname}] Condition {c}: initial {x['initial_correct']}/{x['initial_total']}")
        for nm, m in (("all cases", a), ("initially-correct", i)):
            n = m["n_scenarios"]
            print(f"   {nm}: essential correct {m['essential_correct']}/{n} (retained Supported {m['essential_retained_supported']}/{n}) | "
                  f"irrelevant unnecessary withdrawal {m['irrelevant_unnecessary_withdrawal']}/{n} | redundant correct retention {m['redundant_correct_retention']}/{n} | "
                  f"post-update {m['post_correct']}/{m['post_total']} | scenarios all-3 {m['scenarios_all3_correct']}/{n}")
    print("   paired:", res["paired_scenario_level_all3_correct"]); print("   reference:", res["reference_policies_not_model_runs"])
    print("   missing/unparsed:", res["calls_missing_or_unparsed"])

def selfcheck():
    """Scorer check on SIMULATED policies (not model output)."""
    scen, keys = load("eval"), load_keys("eval")
    assert len(scen) == 12
    for s in scen:
        k = keys[s["id"]]
        assert k["initial_gold"] == "Supported"
        assert sorted(v["type"] for v in k["branches"].values()) == ["essential", "irrelevant", "redundant"]
        assert {v["gold"] for v in k["branches"].values() if v["type"] != "essential"} == {"Supported"}
        assert [v["gold"] for v in k["branches"].values() if v["type"] == "essential"] == ["Insufficient evidence"]
        for c in CONDS:  # no key leakage into prompts
            p = initial_prompt(s, c)
            for w in ("essential", "irrelevant", "redundant", "near-miss", "gold"): assert w not in p.lower(), (s["id"], w)
    a, b = initial_prompt(scen[0], "A"), initial_prompt(scen[0], "B")
    assert a.split("Output format")[0] == b.split("Output format")[0], "conditions must share rules+evidence"
    def sim(policy):
        rows = []
        for s in scen:
            k = keys[s["id"]]
            for c in CONDS:
                rows.append(dict(scenario=s["id"], condition=c, stage="init", parsed_decision=policy(k["initial_gold"]), parsed_relies_on=[]))
                for bb, kb in k["branches"].items():
                    rows.append(dict(scenario=s["id"], condition=c, stage="br" + bb, parsed_decision=policy(kb["gold"]), parsed_relies_on=[]))
        return score_rows(rows, scen, keys)["conditions"]["A"]
    o = sim(lambda g: g); assert o["all_cases"]["post_correct"] == 36 and o["initial_correct"] == 12
    ab = sim(lambda g: "Insufficient evidence")
    assert ab["initial_correct"] == 0 and ab["all_cases"]["post_correct"] == 12 and ab["all_cases"]["irrelevant_unnecessary_withdrawal"] == 12
    assert ab["initially_correct_cases"]["n_scenarios"] == 0
    ks = sim(lambda g: "Supported")
    assert ks["all_cases"]["post_correct"] == 24 and ks["all_cases"]["essential_retained_supported"] == 12
    assert parse("x\nRELIES_ON: S1, S4\n**DECISION:** Insufficient evidence.")== ("Insufficient evidence", ["S1", "S4"])
    assert parse("no label")[0] == "UNPARSED" and parse(None)[0] == "MISSING"
    assert abs(sign_test(0, 5) - 0.0625) < 1e-9 and sign_test(0, 0) == 1.0
    print("selfcheck OK: oracle 36/36, always-abstain 12/36 (0/12 initial), always-Supported 24/36; parser + sign test OK")

def freeze():
    files = ["build_dataset.py", "pts.py", "PROTOCOL.md", "data/eval_scenarios.json", "keys/eval_keys.json",
             "data/practice_scenarios.json", "keys/practice_keys.json"]
    h = {f: hashlib.sha256(open(f"{HERE}/{f}", "rb").read()).hexdigest() for f in files}
    json.dump(dict(frozen_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), sha256=h),
              open(f"{HERE}/FREEZE.json", "w"), indent=1)
    print(json.dumps(h, indent=1))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--set", default="eval")
    a = ap.parse_args()
    {"prepare-initial": lambda: prepare_initial(a.set), "prepare-branches": lambda: prepare_branches(a.set),
     "ingest": lambda: ingest(a.set), "score": lambda: score(a.set), "selfcheck": selfcheck, "freeze": freeze}[a.cmd]()
