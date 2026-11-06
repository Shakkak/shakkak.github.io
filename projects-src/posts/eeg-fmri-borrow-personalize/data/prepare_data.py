"""Build the small tables this post plots from the public code companion's result files.

Run from anywhere with the companion repository checked out:
    python prepare_data.py /path/to/Borrow-then-Personalize-EEG-fMRI-Brain-Encoding-with-Limited-Labels
It uses the same helper functions that draw the paper's figures, so every number here is a number in the paper.
"""
import csv
import sys
from pathlib import Path

import numpy as np

repo = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(repo / "scripts"))
import plot_paper_v3 as v3  # noqa: E402
import plot_paper_v5 as v5  # noqa: E402

out = Path(__file__).resolve().parent

# 1. THINGS-EEG1, 24 new people: own model, borrowing and the shared network
people, own, avg, avg_p1, core = v3._per_person_eeg1()
with open(out / "eeg1_people.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["person", "own_model", "borrowing", "borrowing_first_test", "shared_network"])
    for row in zip(people, own, avg, avg_p1, core):
        w.writerow([row[0]] + [round(float(x), 4) for x in row[1:]])

# 2. The personal map minus borrowing, every prespecified test, one value per person
n = v3.load("08n_eeg1_h4b_confirmation/08n_decision.json")
a = v3.load("09a_eeg2_h4b_replication/09a_decision.json")
l = v3.load("09l_alljoined_confirmation/09l_decision.json")["primary"]
c = v3.load("10c_nsd_confirmation/10c_summary.json")["claims"]
enc, _ = v3._nsd_person_diffs()
_, _, e3 = v3._nod_person_diffs()
nsd_ids = sorted({r["subject"] for r in csv.DictReader(open(repo / "results/10c_nsd_confirmation/10c_scores.csv"))})
nod_ids = sorted({r["subject"] for r in csv.DictReader(open(repo / "results/11d_nod_confirmation/11d_scores.csv"))
                  if r["threshold"] == "0.05" and r["centred"] == "False"})
tests = [("THINGS-EEG1", "lab EEG", list(n["d"]), [v[0] for v in n["d"].values()], n["per_comparator"]["avg_sources"], n["delta"]),
         ("THINGS-EEG2", "lab EEG", list(a["d"]), [v[0] for v in a["d"].values()], a["per_comparator"]["avg_sources"], a["delta"]),
         ("Alljoined", "consumer EEG", list(l["d"]), [v[0] for v in l["d"].values()], l["claims"]["C1"], l["delta"]),
         ("NSD", "7 T fMRI", nsd_ids, enc, c["C1_lowrank_map_minus_avg_enc_r"],
          c["C1_lowrank_map_minus_avg_enc_r"]["margin"]),
         ("NOD", "3 T fMRI, single trials", nod_ids, e3, v5._bounds(e3, 3), 0.011)]
with open(out / "map_gain_people.csv", "w", newline="") as f, open(out / "map_gain_tests.csv", "w", newline="") as g:
    w, s = csv.writer(f), csv.writer(g)
    w.writerow(["dataset", "person", "gain"])
    s.writerow(["dataset", "kind", "n", "positive", "mean", "lower", "upper", "margin", "verdict"])
    for name, kind, ids, vals, b, margin in tests:
        vals = np.asarray(vals, float)
        for p, v in zip(ids, vals):
            w.writerow([name, p, round(float(v), 4)])
        s.writerow([name, kind, len(vals), int((vals > 0).sum()), round(float(b["mean"]), 4), round(float(b["lower"]), 4),
                    round(float(b["upper"]), 4), round(float(margin), 4), v3.row_verdict(b["lower"], b["upper"], margin)])

# 3. NSD identification among 200 images by number of labelled images (centred scores, ridge donors)
keep = {("map", "ridge"), ("own_ridge", "-"), ("combination", "ridge"), ("borrowing", "ridge")}
with open(repo / "results/10k_nsd_budget_curve/results/metrics/10k_scores.csv") as f, open(out / "nsd_budget.csv", "w", newline="") as g:
    w = csv.writer(g)
    w.writerow(["person", "method", "k", "top1"])
    for r in csv.DictReader(f):
        if (r["method"], r["donors"]) in keep:
            w.writerow([r["subject"], r["method"], r["k"], r["top1_centred"]])

# 4. THINGS-EEG2: gain over borrowing when each label averages 1, 2 or 4 repetitions
with open(repo / "results/09t_eeg2_label_reps/09t_people.csv") as f, open(out / "label_reps.csv", "w", newline="") as g:
    w = csv.writer(g)
    w.writerow(["person", "map", "k", "repetitions", "gain"])
    for r in csv.DictReader(f):
        for m in ("lowrank", "h4b"):
            for k in (250, 500):
                for reps in (1, 2, 4):
                    w.writerow([r["person"], m, k, reps, round(float(r[f"{m}_k{k}_n{reps}_r_post"]) - float(r["avg_r_post"]), 4)])
print("wrote", sorted(p.name for p in out.glob("*.csv")))
