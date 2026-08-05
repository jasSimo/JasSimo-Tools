"""Project-agnostic, colorblind-safe plotting style.

    from jassimo.plotting import set_style, new_figure, savefig, PALETTE

Everything here is documented in :mod:`jassimo.plotting.style`; import from this
package rather than from that module, so the layout stays free to change.
"""

from jassimo.plotting.style import (
    BOX_GAP,
    CMAP_DIVERGING,
    CMAP_SEQUENTIAL,
    DEFAULT_TARGET,
    PALETTE,
    PALETTE_PRIMARY,
    PALETTE_SECONDARY,
    PANEL_MAX_TICKS,
    PANEL_SCALE,
    PLOT_DPI,
    TARGETS,
    Target,
    active_target,
    legend_outside,
    mask_upper_triangle,
    new_figure,
    savefig,
    set_style,
)

__all__ = [
    "BOX_GAP",
    "CMAP_DIVERGING",
    "CMAP_SEQUENTIAL",
    "DEFAULT_TARGET",
    "PALETTE",
    "PALETTE_PRIMARY",
    "PALETTE_SECONDARY",
    "PANEL_MAX_TICKS",
    "PANEL_SCALE",
    "PLOT_DPI",
    "TARGETS",
    "Target",
    "active_target",
    "legend_outside",
    "mask_upper_triangle",
    "new_figure",
    "savefig",
    "set_style",
]
