"""Draw the post's thumbnail (cover.png, 1200 x 630) from map_gain_people.csv: every person's
gain of the personal map over borrowing, one column per dataset, with each test's margin."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

here = Path(__file__).resolve().parent
people = pd.read_csv(here / "map_gain_people.csv")
tests = pd.read_csv(here / "map_gain_tests.csv")
bg, teal, grey, red = "#0f172a", "#2a9d8f", "#94a3b8", "#e76f51"

fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=bg)
ax = fig.add_axes([0.04, 0.17, 0.92, 0.76], facecolor=bg)
rng = np.random.default_rng(7)
for i, t in tests.iterrows():
    v = people[people.dataset == t.dataset].gain.to_numpy()
    x = i + rng.normal(0, 0.09, len(v))
    ax.scatter(x, v, s=150, color=teal, alpha=0.75, linewidths=0, zorder=3)
    ax.plot([i - 0.32, i + 0.32], [t.margin] * 2, color=red, lw=2.5, ls=(0, (4, 3)), zorder=2)
    ax.text(i, -0.034, t.dataset, color=grey, ha="center", va="top", fontsize=19)
ax.axhline(0, color=grey, lw=1.2, alpha=0.6)
ax.set_xlim(-0.6, len(tests) - 0.4)
ax.set_ylim(-0.03, 0.105)
ax.axis("off")
fig.savefig(here.parent / "cover.png", facecolor=bg, metadata={"Software": None})
