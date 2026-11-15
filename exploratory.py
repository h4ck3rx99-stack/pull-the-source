#!/usr/bin/env python3
"""Exploratory stated-dependency checks (text outputs only). Writes results/exploratory_redundant.json."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))
k = {x["id"]: x for x in json.load(open(f"{H}/keys/eval_keys.json"))}
by = {}
for l in open(f"{H}/runs/eval/log.jsonl"):
    r = json.loads(l); by[(r["scenario"], r["condition"], r["stage"])] = r
out = {}
for c in "AB":
    d = dict(n=0, initial_names_exactly_one_of_redundant_pair=0, initial_names_both=0, withdrawn_redundant_source_was_named=0, of_those_kept_supported_and_named_other=0)
    for s, kk in k.items():
        d["n"] += 1
        b = [b for b, v in kk["branches"].items() if v["type"] == "redundant"][0]
        w = kk["branches"][b]["withdraw"]; req = kk["sources"][w]["supports"]
        pair = [x for x, v in kk["sources"].items() if v["supports"] == req]; other = [x for x in pair if x != w][0]
        rel = by[(s, c, "init")]["parsed_relies_on"]; n = sum(x in rel for x in pair)
        d["initial_names_exactly_one_of_redundant_pair"] += n == 1; d["initial_names_both"] += n == 2
        if w in rel:
            d["withdrawn_redundant_source_was_named"] += 1; r = by[(s, c, "br" + b)]
            d["of_those_kept_supported_and_named_other"] += r["parsed_decision"] == "Supported" and other in (r["parsed_relies_on"] or [])
    out[c] = d
json.dump(out, open(f"{H}/results/exploratory_redundant.json", "w"), indent=1); print(out)
