---
name: plotting
description: "Use whenever creating, editing, or reviewing any data-science plot, chart, figure, or visualization intended for slides, papers, or PDF reports. Triggers on matplotlib/seaborn plotting, bar charts, heatmaps, distributions, scatter plots, or any figure that will be inserted into Google Slides, a LaTeX/manuscript paper, or a PDF. Enforces the project-wide jassimo.plotting style so every figure is colorblind-safe, presentation-sized, and free of clipping/overlap/redundancy. Do NOT use for interactive web visualizations (D3.js) or for UI/design work."
---

# Plotting with jassimo.plotting

All plots in this project go through the `jassimo.plotting` package — the one
source of truth for style, colors, geometry and saving. This skill describes how
to use it correctly and which rules are non-negotiable.

## The core workflow

```python
from jassimo.plotting import set_style, new_figure, savefig, PALETTE, legend_outside

set_style("slides")                  # MANDATORY: set the target medium first
fig, ax = new_figure()               # figure in target geometry (not plt.subplots)
ax.bar(range(5), values, color=PALETTE[0])
ax.set_title("Publication-ready title")
ax.set_xlabel("Category"); ax.set_ylabel("Value")
legend_outside(ax)                   # if a legend is needed
savefig(fig, out_dir, "result_stem") # writes all formats of the target
```

Never set `plt.rcParams` directly, never call `plt.savefig` directly, never
hardcode figsize/DPI/font size/color in the script. All of that comes from
`jassimo.plotting`.

## The three targets — choose deliberately

| Target   | When                                     | Output                |
| -------- | ---------------------------------------- | --------------------- |
| `slides` | Plot goes into Google Slides (16:9)      | PNG, insert at 100 %  |
| `paper`  | Plot goes into a LaTeX/manuscript column | SVG (vector)          |
| `pdf`    | Standalone full-page figure in a report  | PDF + PNG             |

One logical plot for two media → call the same plot function twice with a
different `set_style(...)`, saving into separate subfolders. Do NOT duplicate the
plot code.

## Non-negotiable rules

1. **Judge the result, not the code.** After every plot, look at the produced
   file and actively check: is the font presentation-sized in the target medium?
   Is nothing clipped? Does nothing overlap? Are the colors colorblind-safe?
   Only then does the plot count as finished.

2. **Font size is absolute, not relative.** The figsize is fixed per target and
   the fonts are in absolute pt — that is why the font is the same size with 5
   bars as with 10. Never set the font relative to the amount of data or the
   figure size.

3. **Colors from `PALETTE`** (Okabe–Ito, colorblind-safe). The default cycle is
   already set; explicit colors likewise come from `PALETTE[i]`. No raw hex
   codes in the plot script. Build project-specific named colors in a thin
   project layer on top of `PALETTE`.

4. **The title is publication-ready.** No developer metadata (run IDs, internal
   flags) in the title — those belong in the file name. For filtered data, state
   the exclusion rate (e.g. "33% residues removed"). `n=` in the title always
   means the unfiltered total.

5. **No redundancy.** Every piece of information appears in exactly one place.
   Not the same statement in the title, legend and bar label at once.

6. **Legend outside the axes** via `legend_outside(ax)` (right) or
   `legend_outside(ax, side="bottom")` — the latter is a figure-level legend and
   is how a multi-panel figure gets ONE shared legend instead of one per panel.
   Every color, every marker, every line style in the plot has a concise legend
   entry (≤ 4 words).

7. **Symmetric heatmaps** (M[i,j] == M[j,i]) only as a lower triangular matrix:
   `sns.heatmap(data, mask=mask_upper_triangle(data), ...)`.

8. **Grouped boxes/bars/violins always with `gap=BOX_GAP`**. Without it seaborn
   draws the members of a hue group flush against each other and they read as
   one wide shape.

9. **Multi-panel via `new_figure(nrows=…, ncols=…)`**, never with a hand-written
   `figsize`. That switches on panel mode: canvas height, panel title size, body
   text and tick count are adjusted for the grid, because the target sizes are
   measured for a single axes. `savefig` switches it off again.

10. **All visible texts in English** — titles, axes, ticks, legends, annotations.

## What the package handles automatically

- Colorblind-safe default color cycle.
- `constrained_layout`: nothing gets clipped, with identical pixel dimensions
  across all figures of a family.
- Automatic line wrapping of over-long titles, measured in the real title font.
- Panel mode for grids: sizes, canvas height and tick count.
- Saving in all formats of the target with a single `savefig` call.

## Common mistakes to avoid

- Forgetting `set_style()` → default target `slides`, but better to set it
  explicitly.
- `plt.subplots()` instead of `new_figure()` → wrong geometry, font too small,
  and for a grid no panel mode.
- `plt.savefig()` instead of `savefig()` → wrong format, clipping, wrong DPI.
- Shrinking a slide plot in Slides with the mouse → font-size guarantee violated.
- Writing the same plot twice for paper and slides instead of rendering it twice.
