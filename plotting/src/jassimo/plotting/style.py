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
import matplotlib.ticker as mticker
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
    panel_title: axes-title size in MULTI-PANEL figures. Every other size here is
              measured for ONE axes filling the canvas; a 2x2 panel is a third of
              that width and the full-size bold title both overwhelms it and
              collides with its neighbours. See :func:`new_figure`.
    max_height: tallest figure this medium tolerates, in inches. Multi-panel
              figures grow downwards up to this; for slides it equals the canvas
              height, because the slide itself cannot grow.
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
    panel_title: int
    max_height: float


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
        panel_title=17, max_height=4.5,     # the slide cannot grow
    ),
    "paper": Target(
        name="paper",
        figsize=(6.0, 4.0),
        title=15, suptitle=16, axis=13, tick=11, legend=11, annot=9,
        formats=("svg",),
        seaborn_context="paper",
        # 11 pt, a step below the other targets' panel titles relative to their
        # body text: a column-width canvas leaves the least room per panel, and
        # at 13 pt these titles needed two lines.
        panel_title=11, max_height=9.0,     # one manuscript column
    ),
    "pdf": Target(
        name="pdf",
        # 8 x 5 in, not the 4:3 of a slide deck: at 4:3 this was the squarest of
        # the three canvases, which stretches bars and panels vertically. 1.6:1
        # sits between the paper column and the wide slide.
        figsize=(8.0, 5.0),
        title=17, suptitle=18, axis=15, tick=13, legend=13, annot=10,
        formats=("pdf", "png"),
        seaborn_context="notebook",
        panel_title=15, max_height=9.5,     # one portrait page
    ),
}

DEFAULT_TARGET: Final[str] = "slides"
PLOT_DPI: Final[int] = 300   # for raster outputs (png); vector formats ignore it

# ── Multi-panel tuning (see new_figure) ──────────────────────────────────────
# Panels are a fraction of the canvas, so body text steps down with them and the
# number of ticks is capped — full-size ticks in a third-width panel collide.
PANEL_SCALE: Final[float] = 0.8      # ticks / labels / legend, relative to target
PANEL_MAX_TICKS: Final[int] = 4      # per numeric axis


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

# Gap between the boxes/bars/violins of one hue group, as a fraction of their
# width. Without it seaborn draws the members of a group flush against each
# other and they read as one wide shape. seaborn takes this only as a call
# argument (there is no rcParam), so pass it explicitly:
#     sns.boxplot(..., hue="genotype", gap=BOX_GAP)
BOX_GAP: Final[float] = 0.15


# ═══════════════════════════════════════════════════════════════════════════════
# Legend placement — always outside the axes so it never overlaps data
# ═══════════════════════════════════════════════════════════════════════════════

LEGEND_OUTSIDE_RIGHT: Final[dict[str, Any]] = {
    "bbox_to_anchor": (1.02, 1.0), "loc": "upper left",
    "borderaxespad": 0.0, "frameon": False,
}
# Anchored to the FIGURE, not the axes: constrained_layout reserves the strip
# itself, so the legend clears the tick labels and the x-axis label whatever
# their height. A fixed axes-fraction offset cannot — it used to be drawn
# straight over the x-axis label.
LEGEND_OUTSIDE_BOTTOM: Final[dict[str, Any]] = {
    "loc": "outside lower center", "frameon": False,
}


def legend_outside(ax: Axes, *, side: str = "right", **kwargs: Any) -> None:
    """Place ``ax``'s legend outside the axes area so it never overlaps data.

    ``side="bottom"`` produces a FIGURE-level legend centred under everything —
    which is also how a multi-panel figure gets one shared legend instead of one
    per panel. It requires constrained_layout, which :func:`set_style` enables.

    Args:
        ax:   Axes whose legend entries to use.
        side: ``"right"`` (default) or ``"bottom"`` (wide or multi-panel figures).
        **kwargs: Forwarded to the legend call (e.g. ``handles``, ``labels``,
            ``ncol``, ``title``).
    """
    if side != "bottom":
        ax.legend(**{**LEGEND_OUTSIDE_RIGHT, **kwargs})
        return

    handles = kwargs.pop("handles", None)
    labels = kwargs.pop("labels", None)
    if handles is None or labels is None:
        handles, labels = ax.get_legend_handles_labels()
    existing = ax.get_legend()
    if existing is not None:
        existing.remove()      # seaborn may have put one inside the axes already
    ax.figure.legend(handles, labels, **{**LEGEND_OUTSIDE_BOTTOM, **kwargs})


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


# ═══════════════════════════════════════════════════════════════════════════════
# Panel mode — multi-panel figures need their own sizes, not the single-axes ones
# ═══════════════════════════════════════════════════════════════════════════════
# Entered by new_figure() when a grid is requested, left by savefig(). The state
# is module-level for the same reason set_style()'s is: one figure at a time.

_panel_rc_backup: dict[str, Any] | None = None


def _panel_figsize(t: Target, nrows: int, ncols: int) -> tuple[float, float]:
    """Canvas for a grid: medium-fixed width, height scaled by rows-per-column.

    Scaling by rows ALONE stretches the figure: a second column already gives
    each panel its width back, so growing the height on top leaves tall, narrow
    panels (a 2x2 pdf came out 8 x 9.5 in, taller than it is wide). Rows over
    columns keeps every panel at roughly the proportions of the single-axes
    canvas. Never below the base height — a single row of panels stays as tall as
    a normal figure — and never above what the medium takes.
    """
    width, height = t.figsize
    scaled = height * (nrows / ncols)
    return (width, min(max(scaled, height), t.max_height))


def _enter_panel_mode(t: Target) -> None:
    global _panel_rc_backup
    keys = ("axes.titlesize", "axes.titleweight", "axes.titlelocation",
            "axes.titlepad", "axes.labelsize", "xtick.labelsize",
            "ytick.labelsize", "legend.fontsize", "legend.title_fontsize")
    if _panel_rc_backup is None:          # never overwrite the single-axes values
        _panel_rc_backup = {k: plt.rcParams[k] for k in keys}
    plt.rcParams.update({
        # Bold and centred like a single-axes title, only stepped down in size:
        # a panel title labels its panel without competing with the suptitle.
        # Set it per axes with set_title(loc="left") if a particular figure wants
        # the flush-left panel convention instead.
        "axes.titlesize": t.panel_title,
        "axes.titleweight": "bold",
        "axes.titlelocation": "center",
        "axes.titlepad": 6.0,
        "axes.labelsize": round(t.axis * PANEL_SCALE),
        "xtick.labelsize": round(t.tick * PANEL_SCALE),
        "ytick.labelsize": round(t.tick * PANEL_SCALE),
        "legend.fontsize": round(t.legend * PANEL_SCALE),
        "legend.title_fontsize": round(t.legend * PANEL_SCALE) + 1,
    })


def _exit_panel_mode() -> None:
    global _panel_rc_backup
    if _panel_rc_backup is not None:
        plt.rcParams.update(_panel_rc_backup)
        _panel_rc_backup = None


def _thin_panel_ticks(fig: Figure) -> None:
    """Cap the tick count on plain numeric axes of a panel figure.

    Only axes still carrying matplotlib's default ``AutoLocator`` are touched —
    categorical axes (bar/box plots) and log axes bring their own locator, and
    replacing it would destroy their labels.
    """
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis):
            if type(axis.get_major_locator()) is mticker.AutoLocator:
                axis.set_major_locator(mticker.MaxNLocator(PANEL_MAX_TICKS))


def new_figure(**kwargs: Any) -> tuple[Figure, Any]:
    """``plt.subplots`` pre-sized to the active target's ``figsize``.

    Any keyword is forwarded to ``plt.subplots``; an explicit ``figsize``
    overrides the target default when you truly need a custom size.

    Asking for a grid (``nrows``/``ncols`` beyond 1) switches on PANEL MODE: the
    canvas grows downwards as far as the medium allows, axes titles step down to
    ``Target.panel_title``, and body text scales by
    :data:`PANEL_SCALE`, because every size in :class:`Target` is measured for one
    axes filling the canvas. :func:`savefig` restores the single-axes values.

    Returns:
        ``(fig, ax)`` exactly as ``plt.subplots`` does — ``ax`` is an array for a
        grid.
    """
    nrows, ncols = int(kwargs.get("nrows", 1)), int(kwargs.get("ncols", 1))
    if nrows * ncols > 1:
        kwargs.setdefault("figsize", _panel_figsize(_active, nrows, ncols))
        _enter_panel_mode(_active)
    else:
        kwargs.setdefault("figsize", _active.figsize)
    return plt.subplots(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# Saving — one call writes every format the target declares
# ═══════════════════════════════════════════════════════════════════════════════

_WRAP_PASSES: Final[int] = 3        # wrapping reflows the layout; re-measure
_WRAP_MARGIN_IN: Final[float] = 0.05
_WRAP_MIN_CHARS: Final[int] = 12


def _axes_titles(ax: Axes) -> list[Any]:
    """All title artists of ``ax`` that carry text.

    ``ax.title`` is only the CENTRED one; ``set_title(loc="left")`` — which panel
    mode uses — writes to a separate artist, and a title looked up the wrong way
    would silently never be wrapped.
    """
    candidates = (ax.title,
                  getattr(ax, "_left_title", None),
                  getattr(ax, "_right_title", None))
    return [t for t in candidates if t is not None and t.get_text().strip()]


def _title_budget_in(ax: Axes, title: Any, fig_width_in: float) -> float:
    """Width a title on ``ax`` may occupy without leaving the canvas, in inches.

    The axes width is the natural budget, but a title is anchored to the axes,
    and an axes pushed aside by an outside legend sits off-centre — so a title
    that fits the axes can still overhang the figure edge. Take whichever of the
    two is tighter, measured from the title's own anchor point.
    """
    pos = ax.get_position()
    align = title.get_horizontalalignment()
    if align == "left":
        reach = fig_width_in - pos.x0 * fig_width_in
    elif align == "right":
        reach = pos.x1 * fig_width_in
    else:
        centre = (pos.x0 + pos.x1) / 2.0 * fig_width_in
        reach = 2.0 * min(centre, fig_width_in - centre)
    return max(0.5, min(pos.width * fig_width_in, reach) - _WRAP_MARGIN_IN)


def _rewrap(text: Any, budget_in: float, dpi: float) -> bool:
    """Re-wrap one text to ``budget_in``. Returns True if it changed.

    The line width comes from MEASURING the text in its actual font rather than
    from a characters-per-inch constant: the real value ranges from 5.0 (20 pt
    bold, slides) to 6.7 (15 pt bold, paper), so any single constant is wrong by
    up to 50 % somewhere.
    """
    original = text.get_text()
    if not original.strip():
        return False
    flat = " ".join(original.split())
    text.set_text(flat)
    width_in = text.get_window_extent().width / dpi
    if width_in <= budget_in:
        text.set_text(original)     # fits — keep any manual line breaks as-is
        return False
    chars_per_in = len(flat) / width_in
    max_chars = max(_WRAP_MIN_CHARS, int(budget_in * chars_per_in))
    wrapped = textwrap.fill(flat, width=max_chars)
    text.set_text(wrapped)
    return wrapped != original


def _wrap_all_text(fig: Figure) -> None:
    """Line-wrap axes titles and figure-level texts that would clip the canvas.

    Draws the figure first: constrained_layout only settles the axes positions
    at draw time, so measuring before that reads matplotlib's placeholder
    geometry (0.775 of the figure width) instead of the real one. Wrapping then
    reflows the layout again, hence the repeat until nothing changes.
    """
    fig_width_in = float(fig.get_size_inches()[0])
    fig_budget = fig_width_in - 2 * _WRAP_MARGIN_IN
    for _ in range(_WRAP_PASSES):
        fig.draw_without_rendering()
        changed = False
        for ax in fig.axes:
            for title in _axes_titles(ax):
                changed |= _rewrap(title,
                                   _title_budget_in(ax, title, fig_width_in),
                                   fig.dpi)
        for txt in fig.texts:
            changed |= _rewrap(txt, fig_budget, fig.dpi)
        if not changed:
            return


def savefig(
    fig: Figure,
    out_dir: Path | str,
    name: str,
    *,
    formats: tuple[str, ...] | None = None,
    close: bool = True,
) -> list[Path]:
    """Save ``fig`` into ``out_dir`` as every format the active target declares.

    Thins panel ticks and wraps over-long titles first (so text never clips) and
    writes at the figure's declared ``figsize`` — no tight bbox — so all figures
    in a family share pixel dimensions for side-by-side placement. Vector formats
    (svg/pdf) keep text as real, scalable text; png is written at
    :data:`PLOT_DPI`.

    Also ends panel mode if :func:`new_figure` started one, restoring the
    single-axes font sizes for the next figure.

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
    try:
        if _panel_rc_backup is not None:
            _thin_panel_ticks(fig)
        _wrap_all_text(fig)
        fmts = formats if formats is not None else _active.formats
        paths: list[Path] = []
        for fmt in fmts:
            p = out / f"{name}.{fmt}"
            fig.savefig(p, dpi=PLOT_DPI, format=fmt)
            logger.info("Saved %s", p)
            paths.append(p)
    finally:
        _exit_panel_mode()
    if close:
        plt.close(fig)
    return paths
