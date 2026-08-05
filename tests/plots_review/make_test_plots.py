"""Smoke tests for jassimo.plotting: six figures, rendered for every target.

Each logical plot is written ONCE as a function taking the loaded data and
returning a Figure; the run loop calls it once per target ("slides", "paper",
"pdf") and saves into a per-target subfolder. That is the rule from
plotting-SKILL.md: one logical plot, rendered N times — never duplicated.

Run:
    python make_test_plots.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import seaborn as sns

HERE = Path(__file__).resolve().parent

# Use the installed package when there is one; otherwise fall back to the
# sources of whatever checkout this file happens to sit in. Searching upwards
# rather than hardcoding a depth keeps this working if the folder is moved.
try:
    import jassimo.plotting  # noqa: F401
except ModuleNotFoundError:
    for _parent in HERE.parents:
        _src = _parent / "plotting" / "src"
        if (_src / "jassimo" / "plotting").is_dir():
            sys.path.insert(0, str(_src))
            break
    else:
        raise SystemExit(
            "jassimo.plotting is neither installed nor findable from "
            f"{HERE}. Install it with: uv add --editable <repo>/plotting"
        )

from jassimo.plotting import (  # noqa: E402
    BOX_GAP,
    CMAP_DIVERGING,
    PALETTE,
    PALETTE_PRIMARY,
    PALETTE_SECONDARY,
    active_target,
    legend_outside,
    mask_upper_triangle,
    new_figure,
    savefig,
    set_style,
)

DATA_DIR = HERE / "data"
OUT_DIR = HERE / "plots"
TARGETS = ("slides", "paper", "pdf")

FEATURES = ["hydrophobicity", "charge", "helix_propensity", "disorder_score",
            "flexibility", "sasa", "conservation", "length_zscore"]
METHOD_ORDER = ["baseline", "k-mer", "profile", "cnn", "transformer", "ensemble"]
CONDITION_ORDER = ["control", "low_dose", "high_dose", "washout"]
CLASS_COLORS = {"ordered": PALETTE[0], "partial": PALETTE[2],
                "disordered": PALETTE[3]}


# ── 1. Heatmap — symmetric correlation matrix, lower triangle only ────────────

def plot_correlation_heatmap(data: dict[str, pd.DataFrame]):
    corr = data["features"][FEATURES].corr()
    fig, ax = new_figure()
    # No square=True: on the 10 x 4.5 in slides canvas square cells collapse to a
    # narrow block and the annotations overlap. Letting the cells fill the canvas
    # keeps every number readable at the target's annotation size.
    sns.heatmap(
        corr, mask=mask_upper_triangle(corr), cmap=CMAP_DIVERGING,
        vmin=-1, vmax=1, center=0, linewidths=0.5,
        annot=True, fmt=".2f", annot_kws={"size": active_target().annot},
        cbar_kws={"label": "Pearson r", "shrink": 0.85}, ax=ax,
    )
    ax.set_title("Feature correlation (n=200 samples)")
    ax.tick_params(axis="x", rotation=45)
    ax.tick_params(axis="y", rotation=0)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    return fig


# ── 2. Bar plot — mean F1 per method with SEM error bars ──────────────────────

def plot_method_bars(data: dict[str, pd.DataFrame]):
    stats = (data["methods"].groupby("method")["f1"]
             .agg(["mean", "sem"]).reindex(METHOD_ORDER))
    fig, ax = new_figure()
    ax.bar(stats.index, stats["mean"], yerr=stats["sem"], capsize=4,
           color=PALETTE_PRIMARY, ecolor=PALETTE[7], zorder=3)
    ax.set_title("Ensemble beats every single model (12 replicates, mean ± SEM)")
    ax.set_xlabel("Method")
    ax.set_ylabel("F1 score")
    ax.set_ylim(0, 1.0)
    ax.tick_params(axis="x", rotation=20)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    return fig


# ── 3. Box plot — response by condition, split by genotype ────────────────────

def plot_response_boxes(data: dict[str, pd.DataFrame]):
    fig, ax = new_figure()
    sns.boxplot(
        data=data["groups"], x="condition", y="response", hue="group",
        order=CONDITION_ORDER, hue_order=["wild_type", "mutant"],
        palette=[PALETTE_PRIMARY, PALETTE_SECONDARY], fliersize=3,
        linewidth=1.2, gap=BOX_GAP, ax=ax,
    )
    ax.set_title("Dose response is amplified in the mutant (n=60 per box)")
    ax.set_xlabel("Condition")
    ax.set_ylabel("Response (a.u.)")
    handles, labels = ax.get_legend_handles_labels()
    legend_outside(ax, handles=handles, labels=labels, title="Genotype")
    return fig


# ── 4. Complex — 2x2 dashboard: scatter, density, time course, composition ────

def plot_dashboard(data: dict[str, pd.DataFrame]):
    feats, tc, comp = data["features"], data["timecourse"], data["composition"]
    fig, axes = new_figure(nrows=2, ncols=2)
    (ax_sc, ax_kde), (ax_tc, ax_comp) = axes

    # (a) scatter, colored by class
    for cls in ("ordered", "disordered"):
        sub = feats[feats["class"] == cls]
        ax_sc.scatter(sub["hydrophobicity"], sub["disorder_score"], s=14,
                      alpha=0.75, color=CLASS_COLORS[cls], label=cls)
    ax_sc.set_title("A  Feature space")
    ax_sc.set_xlabel("Hydrophobicity (z)")
    ax_sc.set_ylabel("Disorder score (z)")
    # No legend here: the class colors are shared with B and D and are covered
    # by the one figure-level legend at the bottom.

    # (b) density of the same classes — colors carry over, no second legend
    for cls in ("ordered", "disordered"):
        sns.kdeplot(data=feats[feats["class"] == cls], x="flexibility",
                    fill=True, alpha=0.4, linewidth=1.5,
                    color=CLASS_COLORS[cls], ax=ax_kde)
    ax_kde.set_title("B  Flexibility density")
    ax_kde.set_xlabel("Flexibility (z)")
    ax_kde.set_ylabel("Density")

    # (c) time course: mean line + 95 % CI band across replicates
    agg = (tc.groupby(["condition", "time_h"])["signal"]
           .agg(["mean", "sem"]).reset_index())
    for i, cond in enumerate(["control", "treated", "rescue"]):
        s = agg[agg["condition"] == cond]
        ax_tc.plot(s["time_h"], s["mean"], color=PALETTE[i], label=cond)
        ax_tc.fill_between(s["time_h"], s["mean"] - 1.96 * s["sem"],
                           s["mean"] + 1.96 * s["sem"],
                           color=PALETTE[i], alpha=0.2, linewidth=0)
    ax_tc.set_title("C  Time course")
    ax_tc.set_xlabel("Time (h)")
    ax_tc.set_ylabel("Signal (a.u.)")
    legend_outside(ax_tc)

    # (d) stacked composition per condition — horizontal, so the condition names
    # need no rotation in a panel this narrow
    comp = comp.reindex(CONDITION_ORDER[::-1])
    left = None
    for cls in ("ordered", "partial", "disordered"):
        ax_comp.barh(comp.index, comp[cls], left=left,
                     color=CLASS_COLORS[cls], label=cls, zorder=3)
        left = comp[cls] if left is None else left + comp[cls]
    ax_comp.set_title("D  Class composition")
    ax_comp.set_xlabel("Share (%)")
    ax_comp.set_ylabel("Condition")

    # One shared legend for the class colors, under the whole figure.
    legend_outside(ax_comp, side="bottom", ncol=3)
    fig.suptitle("Treatment shifts structure class and signal kinetics")
    return fig


# ── 5. Complex — annotated, signed heatmap over models x datasets ─────────────

def plot_delta_heatmap(data: dict[str, pd.DataFrame]):
    delta = data["delta"]
    fig, ax = new_figure()
    sns.heatmap(
        delta, cmap=CMAP_DIVERGING, center=0, annot=True, fmt="+.1f",
        annot_kws={"size": active_target().annot}, linewidths=0.5,
        cbar_kws={"label": "Δ accuracy (pp)", "shrink": 0.85}, ax=ax,
    )
    ax.set_title("Accuracy change vs. baseline across seven benchmarks")
    ax.set_xlabel("Dataset")
    ax.set_ylabel("Model")
    ax.tick_params(axis="x", rotation=30)
    ax.tick_params(axis="y", rotation=0)
    for label in ax.get_xticklabels():
        label.set_ha("right")
    return fig


# ── 6. Complex — ten categories, log axis, bottom legend, long title ──────────

def plot_runtime_bars(data: dict[str, pd.DataFrame]):
    wide = data["runtime"].pivot(index="tool", columns="hardware",
                                 values="runtime_s")
    order = wide["cpu_16"].sort_values(ascending=False).index
    wide = wide.loc[order]
    x = range(len(wide))
    width = 0.4
    fig, ax = new_figure()
    ax.bar([i - width / 2 for i in x], wide["cpu_16"], width,
           color=PALETTE_PRIMARY, label="16-core CPU", zorder=3)
    ax.bar([i + width / 2 for i in x], wide["gpu_a100"], width,
           color=PALETTE_SECONDARY, label="A100 GPU", zorder=3)
    ax.set_yscale("log")
    ax.set_xticks(list(x))
    ax.set_xticklabels(wide.index, rotation=30, ha="right")
    # 111 characters: wrapped to the measured width of the target's title font.
    ax.set_title(
        "GPU offloading cuts wall-clock time by roughly a factor of three "
        "across all ten aligners in the benchmark suite"
    )
    ax.set_xlabel("Tool")
    ax.set_ylabel("Runtime (s, log scale)")
    legend_outside(ax)
    return fig


# ── 7. Complex — time course with 95 % CI bands, legend below the axes ────────

def plot_timecourse_ci(data: dict[str, pd.DataFrame]):
    agg = (data["timecourse"].groupby(["condition", "time_h"])["signal"]
           .agg(["mean", "sem"]).reset_index())
    fig, ax = new_figure()
    for i, cond in enumerate(["control", "treated", "rescue"]):
        s = agg[agg["condition"] == cond]
        ax.plot(s["time_h"], s["mean"], color=PALETTE[i], linewidth=2.5,
                marker="o", markersize=4, label=cond)
        ax.fill_between(s["time_h"], s["mean"] - 1.96 * s["sem"],
                        s["mean"] + 1.96 * s["sem"],
                        color=PALETTE[i], alpha=0.2, linewidth=0)
    ax.set_title("Treatment response saturates by 16 h, rescue is transient "
                 "(8 replicates, mean ± 95 % CI)")
    ax.set_xlabel("Time (h)")
    ax.set_ylabel("Signal (a.u.)")
    ax.set_xlim(0, 23)
    legend_outside(ax, side="bottom", ncol=3)
    return fig


PLOTS = {
    "01_heatmap_feature_correlation": plot_correlation_heatmap,
    "02_bar_method_scores": plot_method_bars,
    "03_box_response_by_condition": plot_response_boxes,
    "04_complex_dashboard": plot_dashboard,
    "05_complex_delta_heatmap": plot_delta_heatmap,
    "06_complex_runtime_benchmark": plot_runtime_bars,
    "07_complex_timecourse_ci": plot_timecourse_ci,
}


def load_data() -> dict[str, pd.DataFrame]:
    return {
        "features": pd.read_csv(DATA_DIR / "feature_matrix.csv"),
        "methods": pd.read_csv(DATA_DIR / "method_scores.csv"),
        "groups": pd.read_csv(DATA_DIR / "group_values.csv"),
        "timecourse": pd.read_csv(DATA_DIR / "timecourse.csv"),
        "delta": pd.read_csv(DATA_DIR / "model_dataset_delta.csv",
                             index_col="model"),
        "runtime": pd.read_csv(DATA_DIR / "runtime_benchmark.csv"),
        "composition": pd.read_csv(DATA_DIR / "composition.csv",
                                   index_col="condition"),
    }


def main() -> None:
    data = load_data()
    written = 0
    for target in TARGETS:
        set_style(target)
        for name, fn in PLOTS.items():
            fig = fn(data)
            paths = savefig(fig, OUT_DIR / target, name)
            written += len(paths)
            print(f"  {target:6s} {name:32s} -> "
                  f"{', '.join(p.name for p in paths)}")
    print(f"\n{written} files in {OUT_DIR}")


if __name__ == "__main__":
    main()
