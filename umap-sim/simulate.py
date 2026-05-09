#!/usr/bin/env python3
"""
Latent Space UMAP Visualizer
Generates synthetic 2048-d histopathology embeddings per tissue site
and applies UMAP dimensionality reduction.

Usage:
    python simulate.py --pct 15     # UMAP on 15% of all patches (~112k)
    python simulate.py --pct 100    # UMAP on all patches (~750k, needs ~6 GB RAM)
"""

import argparse
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import umap as umap_lib

# ==========================================
# 0. ARGS
# ==========================================
parser = argparse.ArgumentParser(description="Latent space UMAP simulation")
parser.add_argument(
    "--pct", type=float, default=15.0,
    help="Percentage of patches to run UMAP on (0.1–100, default: 15)",
)
args = parser.parse_args()

if not (0.1 <= args.pct <= 100.0):
    print("Error: --pct must be between 0.1 and 100")
    sys.exit(1)

frac = args.pct / 100.0

# ==========================================
# 1. CONSTANTS
# ==========================================
np.random.seed(42)

DIM              = 2048
SCALE            = 12.0   # inter-cluster separation in 2048-d space
NUM_CASES        = 3624
PATCHES_PER_CASE = 207
TOTAL_PATCHES    = NUM_CASES * PATCHES_PER_CASE

site_counts = {
    "Breast":            1098,
    "Bronchus and Lung":  585,
    "Kidney":             537,
    "Prostate":           500,
    "Colon":              454,
    "Stomach":            443,
}
site_counts["Other"] = NUM_CASES - sum(site_counts.values())

n_sample = max(1, int(TOTAL_PATCHES * frac))
est_gb   = n_sample * DIM * 4 / 1e9

print(f"Total patches  : {TOTAL_PATCHES:,}")
print(f"Sample ({args.pct:.1f}%)  : {n_sample:,} patches")
print(f"Vector matrix  : ~{est_gb:.2f} GB  (float32, {n_sample:,} × {DIM})")
if est_gb > 4:
    print("  ⚠  Large memory footprint — consider a lower --pct if RAM is limited")
print()

# ==========================================
# 2. BUILD CASE / PATCH METADATA
#    Noise profile is set per-case (same as original),
#    then repeated for each of the 207 patches in that case.
# ==========================================
print("Building patch metadata...")

cases_data = []
case_id_counter = 0
for site, count in site_counts.items():
    for _ in range(count):
        case_id_counter += 1
        noise = np.random.choice(
            ["Core", "Edge", "Half_Global", "Global"],
            p=[0.83, 0.15, 0.015, 0.005],
        )
        cases_data.append({
            "Case_ID":       f"WSI_{case_id_counter:04d}",
            "Primary_Site":  site,
            "Noise_Profile": noise,
        })

df_cases   = pd.DataFrame(cases_data)
df_patches = (
    df_cases
    .loc[df_cases.index.repeat(PATCHES_PER_CASE)]
    .reset_index(drop=True)
)

# ==========================================
# 3. STRATIFIED SAMPLE (proportional per site)
# ==========================================
if frac < 1.0:
    df_sample = (
        df_patches
        .groupby("Primary_Site", group_keys=False)
        .apply(lambda g: g.sample(frac=frac, random_state=42))
        .reset_index(drop=True)
    )
else:
    df_sample = df_patches.copy()

n = len(df_sample)

print("Sample breakdown:")
for site, cnt in df_sample["Primary_Site"].value_counts().sort_index().items():
    print(f"  {site:<22} {cnt:>8,} patches")
print()

# ==========================================
# 4. TISSUE BASIS VECTORS  (2048-d)
#
#    Each tissue gets a random unit vector scaled to SCALE.
#    Colon & Stomach share 50% of a common GI component →
#    their means are closer than all other pairs, so UMAP
#    places them near each other but still separable.
# ==========================================
print("Generating tissue-specific 2048-d basis vectors...")

rng_basis = np.random.RandomState(0)
raw = {site: rng_basis.randn(DIM).astype(np.float32) for site in site_counts}

gi_shared         = rng_basis.randn(DIM).astype(np.float32)
raw["Colon"]   = 0.5 * gi_shared + 0.5 * raw["Colon"]
raw["Stomach"] = 0.5 * gi_shared + 0.5 * raw["Stomach"]

tissue_bases = {
    site: (vec / np.linalg.norm(vec)) * SCALE
    for site, vec in raw.items()
}

# Verify Colon–Stomach cosine similarity is ~0.5
col = tissue_bases["Colon"]
sto = tissue_bases["Stomach"]
sim = np.dot(col, sto) / (np.linalg.norm(col) * np.linalg.norm(sto))
print(f"  Colon–Stomach cosine similarity: {sim:.3f}  (target ≈ 0.5)")
print()

# ==========================================
# 5. CASE-LEVEL DRIFT  (simulates WSI batch effect)
# ==========================================
rng_drift    = np.random.RandomState(99)
unique_cases = df_sample["Case_ID"].unique()
case_drift   = {
    case: rng_drift.randn(DIM).astype(np.float32) * 0.4
    for case in unique_cases
}

# ==========================================
# 6. GENERATE 2048-d EMBEDDING VECTORS
#
#    patch_vector = tissue_base + case_drift + noise(profile)
#
#    Noise profiles:
#      Core       → tight Gaussian (σ = 1.0)
#      Edge       → wider Gaussian (σ = 2.5)
#      Half_Global→ 50% tissue signal + 50% broad random
#      Global     → fully random scatter across 2048-d space
# ==========================================
print(f"Allocating {n:,} × {DIM} float32 array...")

# --- tissue base (fancy-indexed, no Python loop) ---
site_list   = list(site_counts.keys())
site_to_idx = {s: i for i, s in enumerate(site_list)}
site_codes  = np.array([site_to_idx[s] for s in df_sample["Primary_Site"].values])
base_stack  = np.vstack([tissue_bases[s] for s in site_list])   # (7, 2048)
vectors     = base_stack[site_codes].copy()                      # (n, 2048)

# --- case drift (fancy-indexed) ---
case_list   = list(unique_cases)
case_to_idx = {c: i for i, c in enumerate(case_list)}
case_codes  = np.array([case_to_idx[c] for c in df_sample["Case_ID"].values])
drift_stack = np.vstack([case_drift[c] for c in case_list])     # (n_cases, 2048)
vectors    += drift_stack[case_codes]

# --- per-patch noise by noise profile ---
rng_noise  = np.random.RandomState(7)
noise_vals = df_sample["Noise_Profile"].values

core_mask = noise_vals == "Core"
edge_mask = noise_vals == "Edge"
half_mask = noise_vals == "Half_Global"
glob_mask = noise_vals == "Global"

if core_mask.sum():
    vectors[core_mask] += (
        rng_noise.randn(core_mask.sum(), DIM).astype(np.float32) * 1.0
    )
if edge_mask.sum():
    vectors[edge_mask] += (
        rng_noise.randn(edge_mask.sum(), DIM).astype(np.float32) * 2.5
    )
if half_mask.sum():
    n_h = half_mask.sum()
    half_noise = rng_noise.randn(n_h, DIM).astype(np.float32) * (SCALE * 0.6)
    vectors[half_mask] = 0.5 * vectors[half_mask] + 0.5 * half_noise
if glob_mask.sum():
    n_g = glob_mask.sum()
    vectors[glob_mask] = rng_noise.randn(n_g, DIM).astype(np.float32) * SCALE

print("Vectors ready.\n")

# ==========================================
# 7. UMAP
# ==========================================
print(f"Running UMAP on {n:,} × {DIM} (cosine metric, may take a while)...")

reducer = umap_lib.UMAP(
    n_components=2,
    n_neighbors=30,
    min_dist=0.1,
    metric="cosine",
    random_state=42,
    low_memory=(n > 100_000),
    verbose=True,
)
embedding = reducer.fit_transform(vectors)

df_sample["DIM_1"] = embedding[:, 0]
df_sample["DIM_2"] = embedding[:, 1]
del vectors   # free RAM before plotting
print("UMAP done.\n")

# ==========================================
# 8. VISUALIZATION
# ==========================================
palette = {
    "Breast":            "#E056FD",
    "Bronchus and Lung": "#7ED6DF",
    "Kidney":            "#F6E58D",
    "Prostate":          "#6AB04C",
    "Colon":             "#EB4D4B",
    "Stomach":           "#BE2EDD",
    "Other":             "#535C68",
}

print("Rendering plot...")
plt.style.use("default")
fig, ax = plt.subplots(figsize=(18, 14), facecolor="white")
ax.set_facecolor("white")

noise_types = {"Half_Global", "Global"}

# Noise/outlier points first (drawn underneath, more transparent)
noise_df = df_sample[df_sample["Noise_Profile"].isin(noise_types)]
for site, grp in noise_df.groupby("Primary_Site"):
    ax.scatter(grp["DIM_1"], grp["DIM_2"],
               c=palette[site], s=8, alpha=0.25, linewidths=0)

# Core / Edge points on top
core_df = df_sample[~df_sample["Noise_Profile"].isin(noise_types)]
for site, grp in core_df.groupby("Primary_Site"):
    ax.scatter(grp["DIM_1"], grp["DIM_2"],
               c=palette[site], s=10, alpha=0.55, linewidths=0)

ax.set_xlabel("UMAP Dimension 1", fontsize=14, fontweight="bold", labelpad=15)
ax.set_ylabel("UMAP Dimension 2", fontsize=14, fontweight="bold", labelpad=15)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.grid(True, color="#EEEEEE", linestyle="-", linewidth=1)

legend_elements = [
    Line2D(
        [0], [0], marker="o", linestyle="None",
        markerfacecolor=color, color="white",
        label=f"{site}  ({site_counts[site] * PATCHES_PER_CASE:,} patches)",
        markersize=12,
    )
    for site, color in palette.items()
    if site_counts.get(site, 0) > 0
]
ax.legend(
    handles=legend_elements,
    bbox_to_anchor=(1.02, 1), loc="upper left",
    fontsize=13, frameon=False,
    title="Primary Organ Site", title_fontsize=15,
)

ax.set_title(
    f"UMAP — Synthetic Histopathology Latent Space\n"
    f"{args.pct:.0f}% sample · n={n:,} patches · {DIM}-d embeddings",
    fontsize=15, pad=20,
)

plt.tight_layout()
out_path = f"umap_{int(args.pct)}pct.png"
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"Saved → {out_path}")
plt.show()
