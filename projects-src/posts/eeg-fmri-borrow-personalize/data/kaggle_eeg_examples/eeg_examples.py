"""Small summaries of THINGS-EEG2's test recordings for the blog post (CC-BY 4.0, Gifford et al. 2022).

Saves averages only: per person the mean response, the mean response to five example images, the 80 single
repeats of one image on channel Oz, and split-half agreement within and between people.
"""
import json
from pathlib import Path

import numpy as np

ROOT = next(p for p in Path("/kaggle/input").rglob("cross-subject-brain-encoding-eeg") if p.is_dir())
meta = np.load(next(ROOT.rglob("image_metadata.npy")), allow_pickle=True).item()
concepts = [c.split("_", 1)[1] for c in meta["test_img_concepts"]]
EXAMPLES = ["banana", "cat", "elephant", "hummingbird", "birthday_cake"]
idx = [concepts.index(c) for c in EXAMPLES]

out = {"source": "THINGS-EEG2 preprocessed test set (Gifford et al. 2022, CC-BY 4.0)", "examples": EXAMPLES,
       "people": [], "mean": [], "images": [], "oz_cat_reps": [], "n_images": 200, "n_reps": 80}
halves = []
for i in range(1, 11):
    f = next(ROOT.rglob(f"sub-{i:02d}/**/preprocessed_eeg_test.npy"), None) or next(
        p for p in ROOT.rglob("*test*.npy") if f"sub-{i:02d}" in str(p))
    d = np.load(f, allow_pickle=True).item()
    x = np.asarray(d["preprocessed_eeg_data"], dtype=np.float32)  # images, reps, channels, times
    if i == 1:
        out["ch_names"] = [str(c) for c in d["ch_names"]]
        out["times"] = np.round(np.asarray(d["times"], dtype=float), 3).tolist()
    oz = out["ch_names"].index("Oz")
    out["people"].append(f"Person {i}")
    out["mean"].append(np.round(x.mean((0, 1)), 3).tolist())
    out["images"].append(np.round(x[idx].mean(1), 3).tolist())
    out["oz_cat_reps"].append(np.round(x[concepts.index("cat"), :, oz], 2).tolist())
    # image-specific part: each half's mean over repeats, minus its mean over images
    h = [x[:, s].mean(1) for s in (slice(0, 40), slice(40, 80))]
    halves.append([(a - a.mean(0, keepdims=True)).ravel() for a in h])
    print(f, x.shape, flush=True)

n = len(halves)
agree = np.zeros((n, n))
for a in range(n):
    for b in range(n):
        agree[a, b] = np.corrcoef(halves[a][0], halves[b][1])[0, 1]
out["half_agreement"] = np.round(agree, 3).tolist()  # diagonal: same person; off-diagonal: two people
Path("/kaggle/working/eeg_examples.json").write_text(json.dumps(out))
print("same person", agree.diagonal().mean().round(3), "two people", agree[~np.eye(n, dtype=bool)].mean().round(3))
