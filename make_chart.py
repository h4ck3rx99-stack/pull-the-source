#!/usr/bin/env python3
"""Results chart. Reads ONLY results/eval_scores.json (derived from recorded outputs)."""
import json, os, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
H = os.path.dirname(os.path.abspath(__file__)); r = json.load(open(f"{H}/results/eval_scores.json"))
C = r["conditions"]; ref = r["reference_policies_not_model_runs"]
def row(c):
    a = C[c]["all_cases"]; n = a["n_scenarios"]
    return [(C[c]["initial_correct"], C[c]["initial_total"]), (a["essential_correct"], n), (a["irrelevant_correct"], n), (a["redundant_correct_retention"], n)]
labels = ["Initial decision\n(gold: Supported)", "Essential source withdrawn\n(gold: Insufficient evidence)", "Irrelevant source withdrawn\n(gold: Supported)", "One of two supports withdrawn\n(gold: Supported)"]
fig, ax = plt.subplots(figsize=(10, 5.2), dpi=160); fig.patch.set_facecolor("#fcfcfb"); ax.set_facecolor("#fcfcfb")
w = 0.34
for i, (c, col, name) in enumerate([("A", "#2a78d6", "A: ordinary prompt"), ("B", "#eb6834", "B: dependency table")]):
    vals = row(c); xs = [j + (i - 0.5) * (w + 0.03) for j in range(4)]
    ax.bar(xs, [v for v, _ in vals], w, color=col, label=name)
    for x, (v, n) in zip(xs, vals): ax.text(x, v + 0.25, f"{v}/{n}", ha="center", va="bottom", fontsize=10, color="#0b0b0b")
ax.set_xticks(range(4)); ax.set_xticklabels(labels, fontsize=9, color="#52514e")
ax.set_ylim(0, 14.5); ax.set_yticks([0, 3, 6, 9, 12]); ax.set_ylabel("Scenarios answered correctly (of 12)", color="#52514e", fontsize=9)
ax.tick_params(colors="#52514e", length=0); ax.grid(axis="y", color="#e6e5e0", linewidth=0.8); ax.set_axisbelow(True)
for s in ax.spines.values(): s.set_visible(False)
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, fontsize=10)
ax.set_title("Pull the Source: correct decisions by branch, Claude Haiku, 12 scenarios per bar", loc="left", fontsize=12, color="#0b0b0b", pad=22)
pa, pb = C["A"]["all_cases"], C["B"]["all_cases"]; ai, su = ref["always_insufficient"], ref["always_supported"]
ax.text(0, 1.03, f"Post-update total: A {pa['post_correct']}/{pa['post_total']}, B {pb['post_correct']}/{pb['post_total']}.  Reference policies (not model runs): always-abstain {ai['post_correct']}/{ai['post_total']}, always-Supported {su['post_correct']}/{su['post_total']}.",
        transform=ax.transAxes, fontsize=8.5, color="#52514e")
fig.tight_layout(); fig.savefig(f"{H}/results/results_chart.png", facecolor=fig.get_facecolor()); print("chart written")
