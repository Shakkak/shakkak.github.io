"""Keep only what the post plots from eeg_examples.json (the Kaggle output): channel Oz, five example images,
the 80 repeats of "cat", and the split-half agreement matrix.

Usage: python compact.py <eeg_examples.json> ../eeg_examples_small.json
"""
import json
import sys

import numpy as np

d = json.load(open(sys.argv[1]))
oz = d["ch_names"].index("Oz")
small = {
    "source": d["source"], "times": d["times"], "examples": d["examples"], "people": d["people"],
    "mean_oz": np.round(np.array(d["mean"])[:, oz], 2).tolist(),
    "images_oz": np.round(np.array(d["images"])[:, :, oz], 2).tolist(),
    "oz_cat_reps": np.round(np.array(d["oz_cat_reps"]), 1).tolist(),
    "half_agreement": d["half_agreement"],
}
json.dump(small, open(sys.argv[2], "w"))
