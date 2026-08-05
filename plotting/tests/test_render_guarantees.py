"""Regression tests for the guarantees jassimo.plotting makes.

Every promise in the README — presentation-sized fonts, nothing clipped, nothing
overlapping — is a property of the RENDERED figure, invisible in the source. So
each test renders and then measures: ink in the border pixels means clipping,
intersecting text bounding boxes mean overlap.

    pytest plotting/tests
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib.figure import Figure

from jassimo.plotting import (
    PALETTE,
    PANEL_SCALE,
    TARGETS,
    legend_outside,
    new_figure,
    savefig,
    set_style,
)

TARGET_NAMES = sorted(TARGETS)
LONG_TITLE = ("GPU offloading cuts wall-clock time by roughly a factor of three "
              "across all ten aligners in the benchmark suite")


# ── helpers ──────────────────────────────────────────────────────────────────

def _visible_ticklabels(ax):
    """Tick labels matplotlib actually draws — ticks outside the view are kept
    as artists but never rendered, and would fake an overlap."""
    out = []
    for axis in (ax.xaxis, ax.yaxis):
        lo, hi = sorted(axis.get_view_interval())
        for loc, lbl in zip(axis.get_ticklocs(), axis.get_ticklabels()):
            if lo <= loc <= hi and lbl.get_text().strip():
                out.append(lbl)
    return out


def _texts(fig: Figure):
    """Every text artist that must stay clear of the others."""
    out = []
    for ax in fig.axes:
        for title in _titles_of(ax):
            out.append(("title", title))
        for lbl in (ax.xaxis.label, ax.yaxis.label):
            if lbl.get_text().strip():
                out.append(("axis-label", lbl))
        for tick in _visible_ticklabels(ax):
            out.append(("tick", tick))
    for txt in fig.texts:
        if txt.get_text().strip():
            out.append(("figure-text", txt))
    return out


def _titles_of(ax):
    """Centre/left/right title artists carrying text."""
    return [t for t in (ax.title, getattr(ax, "_left_title", None),
                        getattr(ax, "_right_title", None))
            if t is not None and t.get_text().strip()]


def _overlaps(fig: Figure) -> list[str]:
    """Pairs of text artists whose boxes intersect, as readable descriptions."""
    fig.draw_without_rendering()
    items = [(kind, t, t.get_window_extent()) for kind, t in _texts(fig)]
    bad = []
    for i, (kind_a, ta, ba) in enumerate(items):
        for kind_b, tb, bb in items[i + 1:]:
            if ba.overlaps(bb) and ba.width > 0 and bb.width > 0:
                bad.append(f"{kind_a} {ta.get_text()[:28]!r} x "
                           f"{kind_b} {tb.get_text()[:28]!r}")
    return bad


def _border_ink(path) -> bool:
    """True if any non-white pixel touches the outermost row/column."""
    from PIL import Image

    a = np.asarray(Image.open(path).convert("L"))
    return bool((a[0, :] < 250).any() or (a[-1, :] < 250).any()
                or (a[:, 0] < 250).any() or (a[:, -1] < 250).any())


def _simple_figure(title: str = "A perfectly ordinary title"):
    fig, ax = new_figure()
    ax.bar(["alpha", "beta", "gamma"], [3, 5, 4], color=PALETTE[0])
    ax.set_title(title)
    ax.set_xlabel("Category")
    ax.set_ylabel("Value")
    return fig, ax


@pytest.fixture(autouse=True)
def _clean_state():
    yield
    plt.close("all")


# ── the four promises ────────────────────────────────────────────────────────

@pytest.mark.parametrize("target", TARGET_NAMES)
def test_fonts_have_the_declared_absolute_size(target):
    """Rendered point sizes equal the target's, whatever the data volume."""
    t = set_style(target)
    fig, ax = _simple_figure()
    fig.draw_without_rendering()
    assert ax.title.get_fontsize() == t.title
    assert ax.xaxis.label.get_fontsize() == t.axis
    assert ax.get_xticklabels()[0].get_fontsize() == t.tick
    assert tuple(fig.get_size_inches()) == t.figsize


@pytest.mark.parametrize("target", TARGET_NAMES)
def test_nothing_is_clipped(target, tmp_path):
    """A long title, a legend and rotated ticks still fit the fixed canvas."""
    set_style(target)
    fig, ax = _simple_figure(LONG_TITLE)
    ax.plot([0, 1, 2], [1, 3, 2], label="a series")
    ax.tick_params(axis="x", rotation=30)
    legend_outside(ax)
    paths = savefig(fig, tmp_path, "clip", formats=("png",))
    assert not _border_ink(paths[0]), f"{target}: ink touches the canvas border"


@pytest.mark.parametrize("target", TARGET_NAMES)
def test_bottom_legend_clears_the_axis_label(target):
    """Regression: the bottom legend used to be drawn over the x-axis label."""
    set_style(target)
    fig, ax = _simple_figure()
    ax.plot([0, 1], [1, 2], label="a series")
    legend_outside(ax, side="bottom", ncol=2)
    fig.draw_without_rendering()
    legend = fig.legends[0]
    assert not legend.get_window_extent().overlaps(
        ax.xaxis.label.get_window_extent())


@pytest.mark.parametrize("target", TARGET_NAMES)
def test_long_title_wraps_inside_the_canvas(target):
    """Regression: the title was wrapped to a width that did not fit."""
    set_style(target)
    fig, ax = _simple_figure(LONG_TITLE)
    ax.plot([0, 1], [1, 2], label="a series")
    legend_outside(ax)            # shrinks and offsets the axes
    from jassimo.plotting.style import _wrap_all_text

    _wrap_all_text(fig)
    fig.draw_without_rendering()
    box = ax.title.get_window_extent()
    assert box.x0 >= -1 and box.x1 <= fig.get_window_extent().x1 + 1, (
        f"{target}: title spills over the canvas edge")
    assert "\n" in ax.title.get_text(), "a 111-char title should have wrapped"


def test_left_aligned_title_is_wrapped_too():
    """Regression: a loc="left" title lives in a different artist than
    ``ax.title``, and used to be skipped by the wrapping entirely."""
    set_style("slides")
    fig, ax = _simple_figure()
    ax.set_title("")
    ax.set_title(LONG_TITLE, loc="left")
    from jassimo.plotting.style import _wrap_all_text

    _wrap_all_text(fig)
    fig.draw_without_rendering()
    assert "\n" in ax.get_title(loc="left")
    box = _titles_of(ax)[0].get_window_extent()
    assert box.x1 <= fig.get_window_extent().x1 + 1


# ── panel mode ───────────────────────────────────────────────────────────────

@pytest.mark.parametrize("target", TARGET_NAMES)
def test_panel_mode_scales_down_and_grows(target):
    t = set_style(target)
    fig, axes = new_figure(nrows=2, ncols=2)
    ax = axes[0, 0]
    ax.plot([0, 1], [0, 1])
    ax.set_title("A  Panel")
    ax.set_xlabel("x")
    fig.draw_without_rendering()
    title = _titles_of(ax)[0]
    assert title.get_fontsize() == t.panel_title
    assert title.get_horizontalalignment() == "center"
    assert title.get_fontweight() == "bold"
    assert ax.get_title() == "A  Panel"
    assert ax.get_xticklabels()[0].get_fontsize() == round(t.tick * PANEL_SCALE)
    assert fig.get_size_inches()[0] == t.figsize[0]      # width is medium-fixed
    assert fig.get_size_inches()[1] <= t.max_height


@pytest.mark.parametrize("target", TARGET_NAMES)
def test_panel_canvas_keeps_the_panel_proportions(target):
    """Regression: growing per ROW alone left a 2x2 taller than it is wide."""
    t = set_style(target)
    base_aspect = t.figsize[0] / t.figsize[1]
    for nrows, ncols in ((2, 2), (2, 1), (1, 3), (3, 2)):
        fig, _ = new_figure(nrows=nrows, ncols=ncols)
        w, h = fig.get_size_inches()
        panel_aspect = (w / ncols) / (h / nrows)
        from jassimo.plotting.style import _exit_panel_mode

        plt.close(fig)
        _exit_panel_mode()      # no savefig here, so end panel mode by hand
        capped = h >= t.max_height - 1e-9        # the cap may squeeze the aspect
        floored = h <= t.figsize[1] + 1e-9       # so may the base-height floor
        if not (capped or floored):
            assert panel_aspect == pytest.approx(base_aspect, rel=0.01), (
                f"{target} {nrows}x{ncols}: panel aspect {panel_aspect:.2f} "
                f"vs base {base_aspect:.2f}")
        assert 0.5 <= w / h <= 3.0, f"{target} {nrows}x{ncols}: canvas {w}x{h}"


def test_panel_mode_is_restored_by_savefig(tmp_path):
    t = set_style("paper")
    before = plt.rcParams["axes.titlesize"]
    fig, axes = new_figure(nrows=2, ncols=2)
    assert plt.rcParams["axes.titlesize"] == t.panel_title
    savefig(fig, tmp_path, "panel", formats=("png",))
    assert plt.rcParams["axes.titlesize"] == before

    fig2, ax2 = _simple_figure()          # next figure is single-axes again
    fig2.draw_without_rendering()
    assert ax2.title.get_fontsize() == t.title


def test_panel_ticks_are_thinned_but_categories_survive(tmp_path):
    set_style("paper")
    fig, axes = new_figure(nrows=2, ncols=2)
    axes[0, 0].plot(np.linspace(0, 23, 24), np.random.default_rng(0).normal(size=24))
    axes[0, 1].bar(["alpha", "beta", "gamma", "delta"], [1, 2, 3, 4])
    axes[1, 0].set_yscale("log")
    axes[1, 0].plot([1, 2, 3], [1, 10, 100])
    axes[1, 1].plot([0, 1], [0, 1])
    savefig(fig, tmp_path, "ticks", formats=("png",), close=False)
    fig.draw_without_rendering()
    assert len(axes[0, 0].get_xticks()) <= 6            # thinned
    assert [t.get_text() for t in axes[0, 1].get_xticklabels()] == [
        "alpha", "beta", "gamma", "delta"]              # categories untouched
    assert axes[1, 0].get_yscale() == "log"


# ── multi-panel figures obey the same no-overlap promise ─────────────────────

@pytest.mark.parametrize("target", TARGET_NAMES)
def test_panel_figure_has_no_overlapping_text(target):
    set_style(target)
    fig, axes = new_figure(nrows=2, ncols=2)
    rng = np.random.default_rng(0)
    for i, ax in enumerate(np.ravel(axes)):
        ax.plot(np.linspace(0, 23, 24), rng.normal(size=24), color=PALETTE[i])
        ax.set_title(f"{'ABCD'[i]}  Panel {i}")
        ax.set_xlabel("Time (h)")
        ax.set_ylabel("Signal")
    from jassimo.plotting.style import _thin_panel_ticks, _wrap_all_text

    _thin_panel_ticks(fig)
    _wrap_all_text(fig)
    assert not _overlaps(fig), f"{target}: {_overlaps(fig)[:3]}"
