"""Generate synthetic test data for the jassimo.plotting smoke tests.

Writes CSVs into ./data next to this file. Everything is seeded, so re-running
reproduces byte-identical files.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent / "data"
SEED = 20260805


def feature_matrix(rng: np.random.Generator) -> pd.DataFrame:
    """200 samples x 8 features with a deliberate correlation block structure.

    Features 1-3 share a latent factor, 4-5 share another (anti-correlated to
    the first), 6-8 are noise. Gives a heatmap with visible structure.
    """
    n = 200
    latent_a = rng.normal(size=n)
    latent_b = rng.normal(size=n)
    cols = {
        "hydrophobicity": 0.90 * latent_a + 0.44 * rng.normal(size=n),
        "charge": 0.80 * latent_a + 0.60 * rng.normal(size=n),
        "helix_propensity": 0.70 * latent_a + 0.71 * rng.normal(size=n),
        "disorder_score": -0.85 * latent_a + 0.53 * rng.normal(size=n),
        "flexibility": 0.75 * latent_b + 0.66 * rng.normal(size=n),
        "sasa": 0.65 * latent_b + 0.76 * rng.normal(size=n),
        "conservation": rng.normal(size=n),
        "length_zscore": rng.normal(size=n),
    }
    df = pd.DataFrame(cols)
    df.insert(0, "sample_id", [f"S{i:03d}" for i in range(n)])
    # A binary class label that actually depends on the latent factor, so the
    # scatter panel shows two separable clouds instead of one blob.
    df["class"] = np.where(latent_a + 0.4 * rng.normal(size=n) > 0,
                           "ordered", "disordered")
    return df


def method_scores(rng: np.random.Generator) -> pd.DataFrame:
    """Six methods x 12 replicates of an F1 score -> bar plot with error bars."""
    means = {"baseline": 0.61, "k-mer": 0.68, "profile": 0.74,
             "cnn": 0.79, "transformer": 0.84, "ensemble": 0.86}
    rows = []
    for method, mu in means.items():
        for rep in range(1, 13):
            rows.append({"method": method, "replicate": rep,
                         "f1": float(np.clip(rng.normal(mu, 0.035), 0, 1))})
    return pd.DataFrame(rows)


def group_values(rng: np.random.Generator) -> pd.DataFrame:
    """4 conditions x 2 groups x 60 observations -> grouped box plot.

    Conditions differ in location, groups differ in spread, and one condition
    carries outliers so the whiskers/fliers get exercised.
    """
    rows = []
    offsets = {"control": 0.0, "low_dose": 0.6, "high_dose": 1.4, "washout": 0.3}
    for condition, off in offsets.items():
        for group, scale in (("wild_type", 1.0), ("mutant", 1.6)):
            vals = rng.normal(4.0 + off, 0.8 * scale, size=60)
            if condition == "high_dose" and group == "mutant":
                vals = np.append(vals, rng.normal(11.0, 0.5, size=4))  # outliers
            for v in vals:
                rows.append({"condition": condition, "group": group,
                             "response": float(v)})
    return pd.DataFrame(rows)


def timecourse(rng: np.random.Generator) -> pd.DataFrame:
    """Signal over 24 time points, 3 conditions, 8 replicates -> line + CI."""
    times = np.arange(0, 24)
    rows = []
    shapes = {
        "control": lambda t: 1.0 + 0.02 * t,
        "treated": lambda t: 1.0 + 2.4 / (1 + np.exp(-(t - 10) / 2.0)),
        "rescue": lambda t: 1.0 + 1.2 * np.exp(-((t - 12) ** 2) / 18.0),
    }
    for condition, fn in shapes.items():
        for rep in range(8):
            noise = rng.normal(0, 0.18, size=times.size)
            drift = rng.normal(0, 0.12)
            for t, y in zip(times, fn(times) + noise + drift):
                rows.append({"time_h": int(t), "condition": condition,
                             "replicate": rep, "signal": float(y)})
    return pd.DataFrame(rows)


def model_dataset_delta(rng: np.random.Generator) -> pd.DataFrame:
    """5 models x 7 datasets, accuracy delta vs. baseline in percentage points.

    Signed values centred near zero -> exercises the diverging colormap and the
    per-target annotation font size.
    """
    models = ["k-mer", "profile", "cnn", "transformer", "ensemble"]
    datasets = ["casp14", "casp15", "cameo", "pdb_hold", "afdb_sub",
                "disprot", "mobidb"]
    strength = dict(zip(models, [-1.5, 1.0, 3.2, 5.0, 6.1]))
    data = {
        ds: [round(float(strength[m] + rng.normal(0, 1.6)), 1) for m in models]
        for ds in datasets
    }
    return pd.DataFrame(data, index=pd.Index(models, name="model"))


def runtime_benchmark(rng: np.random.Generator) -> pd.DataFrame:
    """10 tools x 2 hardware settings -> many-category grouped bar plot.

    Ten categories is the font-size stress test: the fonts must stay identical
    to the six-bar plot.
    """
    tools = ["blast", "diamond", "mmseqs2", "hmmer", "foldseek", "usearch",
             "vsearch", "cd-hit", "minimap2", "bowtie2"]
    rows = []
    for i, tool in enumerate(tools):
        base = 120.0 * np.exp(-0.25 * i) + 4.0
        rows.append({"tool": tool, "hardware": "cpu_16",
                     "runtime_s": round(float(base * rng.uniform(0.9, 1.1)), 1)})
        rows.append({"tool": tool, "hardware": "gpu_a100",
                     "runtime_s": round(float(base * rng.uniform(0.25, 0.45)), 1)})
    return pd.DataFrame(rows)


def composition(rng: np.random.Generator) -> pd.DataFrame:
    """Per-condition class composition in percent -> stacked bar panel."""
    conditions = ["control", "low_dose", "high_dose", "washout"]
    rows = []
    for cond in conditions:
        raw = rng.dirichlet([6, 3, 1.5]) * 100
        rows.append({"condition": cond, "ordered": round(float(raw[0]), 1),
                     "partial": round(float(raw[1]), 1),
                     "disordered": round(float(raw[2]), 1)})
    return pd.DataFrame(rows).set_index("condition")


def main() -> None:
    rng = np.random.default_rng(SEED)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    tables = {
        "feature_matrix.csv": (feature_matrix(rng), False),
        "method_scores.csv": (method_scores(rng), False),
        "group_values.csv": (group_values(rng), False),
        "timecourse.csv": (timecourse(rng), False),
        "model_dataset_delta.csv": (model_dataset_delta(rng), True),
        "runtime_benchmark.csv": (runtime_benchmark(rng), False),
        "composition.csv": (composition(rng), True),
    }
    for fname, (df, with_index) in tables.items():
        path = DATA_DIR / fname
        df.to_csv(path, index=with_index)
        print(f"wrote {path}  ({df.shape[0]} rows x {df.shape[1]} cols)")


if __name__ == "__main__":
    main()
