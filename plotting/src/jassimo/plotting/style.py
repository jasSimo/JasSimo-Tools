"""Project-agnostic plotting style: one source of truth for every DS project.

Import this in ANY data-science / bioinformatics / ML project and every figure
comes out consistent, colorblind-safe, and correctly sized for its final medium
(slides, paper, or a standalone PDF) — without per-project eyeballing.

═══════════════════════════════════════════════════════════════════════════════
THE ONE IDEA: a figure is rendered for exactly ONE target medium.
═══════════════════════════════════════════════════════════════════════════════
The target ("slides" | "paper" | "pdf") fixes BOTH the figure geometry and the
absolute font sizes, so text has a *guaranteed, measured* height in its final
medium instead of a guessed point value. This is why slide text is so often too
small: seaborn's "paper" context scales fonts DOWN, but a figure shrunk onto a
slide needs them LARGER. Choosing the target up front removes the guesswork.

One logical plot → render once per target you need (two calls, two files). Do
NOT try to make a single file auto-scale across media — the viewport differs and
you lose the guarantee.

Quick start
-----------
    from ds_plotting import set_style, savefig, new_figure, PALETTE

    set_style("slides")                 # once at the top of a run
    fig, ax = new_figure()              # figure pre-sized for the target
    ax.bar(x, y, color=PALETTE[0])
    ax.set_title("Result")
    savefig(fig, out_dir, "result")     # writes result.png (slides) 1:1 @100%

Target reference
----------------
    slides — Google Slides 16:9. Slide = 10 × 5.625 in (960 × 540 px @ 96 DPI).
             Slide title 25 pt, page number 10 pt. Figures are full slide width,
             sized to sit UNDER the title bar, and INSERTED AT 100 % (no drag).
             At 100 %, 1 matplotlib-pt = 1 slide-pt, so the 20 pt plot title
             reads one clean step below the 25 pt slide title. Output: PNG.
    paper  — One manuscript/LaTeX column. Small figure read at column width;
             smaller absolute fonts are correct. Output: SVG (vector, crisp,
             searchable text).
    pdf    — A standalone full-page PDF figure (reports, appendices). Output:
             PDF (vector) + PNG preview.
"""

from __future__ import annotations

import logging
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Targets: geometry + fonts + output formats, one dataclass per medium
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class Target:
    """Everything that depends on the output medium, in one place.

    figsize:  (width, height) in inches — the CANVAS. Fonts below are absolute
              point sizes on that canvas, so they translate 1:1 to the medium
              when the figure is placed at 100 %.
    formats:  file types savefig() writes, in order. First one is the "primary".
    seaborn_context: seaborn scaling context; we override exact sizes anyway,
              but this keeps line widths / marker sizes sensibly scaled.
    """

    name: str
    figsize: tuple[float, float]
    title: int
    suptitle: int
    axis: int
    tick: int
    legend: int
    annot: int          # heatmap cell annotations — may be smaller than body text
    formats: tuple[str, ...]
    seaborn_context: str


# Google Slides geometry is exact: 10 × 5.625 in @ 96 DPI = 960 × 540 px.
# Height 4.5 in leaves the title bar (~0.9 in) and page number (~0.2 in) clear.
# Fonts derived so the 20 pt title sits one step under the 25 pt slide title and
# ticks (15 pt) stay above the 10 pt page number — all verified in points.
TARGETS: Final[dict[str, Target]] = {
    "slides": Target(
        name="slides",
        figsize=(10.0, 4.5),
        title=20, suptitle=22, axis=17, tick=15, legend=15, annot=13,
        formats=("png",),
        seaborn_context="talk",
    ),
    "paper": Target(
        name="paper",
        figsize=(6.0, 4.0),
        title=15, suptitle=16, axis=13, tick=11, legend=11, annot=9,
        formats=("svg",),
        seaborn_context="paper",
    ),
    "pdf": Target(
        name="pdf",
        figsize=(8.0, 6.0),
        title=17, suptitle=18, axis=15, tick=13, legend=13, annot=10,
        formats=("pdf", "png"),
        seaborn_context="notebook",
    ),
}

DEFAULT_TARGET: Final[str] = "slides"
PLOT_DPI: Final[int] = 300   # for raster outputs (png); vector formats ignore it


# ═══════════════════════════════════════════════════════════════════════════════
# Colorblind-safe palette (Okabe–Ito) — the scientific standard
# ═══════════════════════════════════════════════════════════════════════════════
# Eight colors distinguishable under all common color-vision deficiencies.
# Reference: Okabe & Ito (2008), "Color Universal Design". Use PALETTE[i] for
# categorical series; it is also installed as the matplotlib color cycle by
# set_style(), so plots that don't specify colors are colorblind-safe by default.

PALETTE: Final[tuple[str, ...]] = (
    "#0072B2",  # blue
    "#E69F00",  # orange
    "#009E73",  # green
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
    "#56B4E9",  # sky blue
    "#F0E442",  # yellow
    "#000000",  # black
)

# Convenience semantic names for the two most common binary contrasts. Projects
# that need domain-specific names (e.g. ordered/disordered) map onto these in
# their own thin layer rather than redefining colors.
PALETTE_PRIMARY: Final[str] = PALETTE[0]
PALETTE_SECONDARY: Final[str] = PALETTE[1]

# Sequential (magnitude) and diverging (signed) colormaps for heatmaps.
CMAP_SEQUENTIAL: Final[str] = "viridis"   # perceptually uniform, CVD-friendly
CMAP_DIVERGING: Final[str] = "RdBu_r"     # signed data centred on white


# ═══════════════════════════════════════════════════════════════════════════════
# Legend placement — always outside the axes so it never overlaps data
# ═══════════════════════════════════════════════════════════════════════════════

LEGEND_OUTSIDE_RIGHT: Final[dict[str, Any]] = {
    "bbox_to_anchor": (1.02, 1.0), "loc": "upper left",
    "borderaxespad": 0.0, "frameon": False,
}
LEGEND_OUTSIDE_BOTTOM: Final[dict[str, Any]] = {
    "bbox_to_anchor": (0.5, -0.18), "loc": "upper center",
    "borderaxespad": 0.0, "frameon": False,
}


def legend_outside(ax: Axes, *, side: str = "right", **kwargs: Any) -> None:
    """Place ``ax``'s legend outside the axes area so it never overlaps data.

    Args:
        ax:   Axes whose legend to place.
        side: ``"right"`` (default) or ``"bottom"`` (wide multi-panel figures).
        **kwargs: Forwarded to ``ax.legend`` (e.g. ``handles``, ``ncol``).
    """
    placement = LEGEND_OUTSIDE_RIGHT if side == "right" else LEGEND_OUTSIDE_BOTTOM
    ax.legend(**{**placement, **kwargs})


# ═══════════════════════════════════════════════════════════════════════════════
# Symmetric-heatmap mask — draw only the lower triangle of symmetric matrices
# ═══════════════════════════════════════════════════════════════════════════════

def mask_upper_triangle(data: np.ndarray | Any) -> np.ndarray:
    """Boolean mask hiding the strict upper triangle of a square matrix.

    Pass as ``mask=`` to ``sns.heatmap`` when M[i,j] == M[j,i] (correlation or
    pairwise matrices): the upper half carries no new information. The diagonal
    stays visible.

    Args:
        data: Square array-like or DataFrame — only ``shape[0]`` is used.
    Returns:
        Boolean ndarray (n, n); True where the cell should be hidden.
    """
    n = data.shape[0] if hasattr(data, "shape") else len(data)
    return np.triu(np.ones((n, n), dtype=bool), k=1)


# ═══════════════════════════════════════════════════════════════════════════════
# Active target + style application
# ═══════════════════════════════════════════════════════════════════════════════

_active: Target = TARGETS[DEFAULT_TARGET]


def set_style(target: str = DEFAULT_TARGET) -> Target:
    """Apply the project-wide style for a render ``target``. Call once per run.

    Sets matplotlib rcParams + seaborn theme, installs the colorblind-safe color
    cycle, and remembers the target so :func:`new_figure` and :func:`savefig`
    use its geometry and formats. Idempotent.

    Args:
        target: ``"slides"`` | ``"paper"`` | ``"pdf"``. See module docstring.
    Returns:
        The active :class:`Target` (useful to read ``.figsize`` etc.).
    Raises:
        KeyError: if ``target`` is not a known target name.
    """
    global _active
    if target not in TARGETS:
        raise KeyError(
            f"unknown target {target!r}; choose from {sorted(TARGETS)}"
        )
    t = TARGETS[target]
    _active = t

    sns.set_theme(context=t.seaborn_context, style="whitegrid",
                  font="DejaVu Sans")
    plt.rcParams.update({
        "figure.figsize": t.figsize,
        "figure.dpi": 100,
        "savefig.dpi": PLOT_DPI,
        # constrained_layout fits titles/labels/legends INSIDE the fixed figsize
        # so nothing clips, while pixel dimensions stay identical across a family
        # (unlike bbox_inches="tight", which would change them per figure).
        "figure.constrained_layout.use": True,
        "font.size": t.tick,
        "axes.titlesize": t.title,
        "axes.titleweight": "bold",
        "axes.titlepad": 12.0,
        "figure.titlesize": t.suptitle,
        "figure.titleweight": "bold",
        "axes.labelsize": t.axis,
        "axes.labelweight": "regular",
        "xtick.labelsize": t.tick,
        "ytick.labelsize": t.tick,
        "legend.fontsize": t.legend,
        "legend.title_fontsize": t.legend + 1,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.prop_cycle": plt.cycler(color=PALETTE),
    })
    return t


def active_target() -> Target:
    """Return the currently active :class:`Target` (set by :func:`set_style`)."""
    return _active


def new_figure(**kwargs: Any) -> tuple[Figure, Axes]:
    """``plt.subplots`` pre-sized to the active target's ``figsize``.

    Any keyword (e.g. ``ncols=2``) is forwarded to ``plt.subplots``; an explicit
    ``figsize`` overrides the target default when you truly need a custom size.

    Returns:
        ``(fig, ax)`` exactly as ``plt.subplots`` does.
    """
    kwargs.setdefault("figsize", _active.figsize)
    return plt.subplots(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# Saving — one call writes every format the target declares
# ═══════════════════════════════════════════════════════════════════════════════

def _wrap_text(text: str, max_chars: int) -> str:
    return textwrap.fill(text, width=max_chars) if len(text) > max_chars else text


def _wrap_all_text(fig: Figure) -> None:
    """Line-wrap axes titles and figure-level texts that would clip the canvas.

    Titles are wrapped to the *axes* width (a centred title is anchored to the
    axes, which may be narrower than the figure after leaving room for a legend);
    figure-level texts use the full figure width.
    """
    width_in = float(fig.get_size_inches()[0])
    fig_max = max(30, round(width_in * 7.5))
    for ax in fig.axes:
        t = ax.get_title()
        if t:
            ax_width_in = ax.get_position().width * width_in
            ax.title.set_text(_wrap_text(t, max(20, round(ax_width_in * 7.5))))
    for txt in fig.texts:
        if txt.get_text():
            txt.set_text(_wrap_text(txt.get_text(), fig_max))


def savefig(
    fig: Figure,
    out_dir: Path | str,
    name: str,
    *,
    formats: tuple[str, ...] | None = None,
    close: bool = True,
) -> list[Path]:
    """Save ``fig`` into ``out_dir`` as every format the active target declares.

    Wraps over-long titles first (so text never clips) and writes at the figure's
    declared ``figsize`` — no tight bbox — so all figures in a family share pixel
    dimensions for side-by-side placement. Vector formats (svg/pdf) keep text as
    real, scalable text; png is written at :data:`PLOT_DPI`.

    Args:
        fig:     The figure to save.
        out_dir: Output directory; created if missing.
        name:    File stem (snake_case, no extension).
        formats: Override the target's formats if needed; default uses them.
        close:   Close the figure afterwards (default True).
    Returns:
        The written paths, one per format.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    _wrap_all_text(fig)
    fmts = formats if formats is not None else _active.formats
    paths: list[Path] = []
    for fmt in fmts:
        p = out / f"{name}.{fmt}"
        fig.savefig(p, dpi=PLOT_DPI, format=fmt)
        logger.info("Saved %s", p)
        paths.append(p)
    if close:
        plt.close(fig)
    return paths
