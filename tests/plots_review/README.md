# jassimo.plotting — test data and test plots

Synthetic data plus seven figures rendered through `jassimo.plotting`, each one
for all three targets. This is the visual counterpart to `../test_render_guarantees.py`:
that one measures, this one is for looking at.

```bash
python generate_test_data.py    # -> data/*.csv   (seeded, reproducible)
python make_test_plots.py       # -> plots/<target>/*
```

Requires matplotlib, seaborn, numpy, pandas. `make_test_plots.py` uses the
installed `jassimo.plotting` if there is one and otherwise finds the sources of
the surrounding checkout, so it runs either way — and keeps running if this
folder is moved.

The PNGs are byte-reproducible across runs; the SVG and PDF outputs are not,
because matplotlib stamps them with a creation date.

## Contents

| Figure                          | Type                    | What it exercises                                       |
| ------------------------------- | ----------------------- | ------------------------------------------------------- |
| `01_heatmap_feature_correlation` | Heatmap                 | `mask_upper_triangle`, diverging colormap, cell annotations |
| `02_bar_method_scores`           | Bar plot                | `PALETTE_PRIMARY`, SEM error bars, two-line title wrap   |
| `03_box_response_by_condition`   | Box plot                | seaborn hue, `BOX_GAP`, outliers, `legend_outside` with a title |
| `04_complex_dashboard`           | 2x2 multi-panel         | panel mode, suptitle, one shared bottom legend, shared class colors |
| `05_complex_delta_heatmap`       | Annotated heatmap       | signed data centred on 0, `active_target().annot`        |
| `06_complex_runtime_benchmark`   | Grouped bars, 10 cats   | log axis, absolute font sizes at 10 categories           |
| `07_complex_timecourse_ci`       | Lines + 95 % CI bands   | `fill_between`, 3 series from the default color cycle    |

Outputs per target, exactly as the target declares: `plots/slides/*.png`,
`plots/paper/*.svg`, `plots/pdf/*.pdf` + `*.png`. 28 files.

Data: 7 CSVs in `data/`, all from `np.random.default_rng(20260805)`.

## Verification

Every slides PNG was inspected visually and checked programmatically for ink in
the outermost pixel column (clipping). All seven are clean. The `paper` and `pdf`
targets were inspected as well.

## Findings — all fixed in the library

Three defects surfaced here and have since been repaired in
`plotting/src/jassimo/plotting/style.py`; each one now has a regression test in
`tests/test_render_guarantees.py`.

**1. `legend_outside(ax, side="bottom")` drew over the x-axis label.** It
anchored at a fixed `(0.5, -0.18)` in axes fractions, which reserves no room for
the axis label, let alone rotated tick labels. It is now a figure-level legend
(`loc="outside lower center"`), so constrained_layout reserves the strip itself.
Test: `test_bottom_legend_clears_the_axis_label`.

**2. Long titles were wrapped too wide and ran off the canvas.** `savefig`
wrapped *before* drawing, so it read matplotlib's placeholder geometry (0.775 of
the figure width) instead of the constrained_layout result (0.689 for figure 06),
and it assumed a constant 7.5 characters per inch where the true value is 5.0 at
the slides title size. Wrapping now happens after a layout pass and measures the
real text. Figure 06 carries its full 111-character title again. Tests:
`test_long_title_wraps_inside_the_canvas`, `test_nothing_is_clipped`.

**3. Multi-panel figures had no usable geometry at `paper`.** Every target
described a single-axes canvas, so a 2x2 grid collided with itself.
`new_figure(nrows=…, ncols=…)` now enters panel mode: the canvas height scales
with rows per column (capped by `Target.max_height`), panel titles drop to
`Target.panel_title`, body text scales by `PANEL_SCALE` and numeric axes are
capped at `PANEL_MAX_TICKS`. Tests: `test_panel_mode_scales_down_and_grows`,
`test_panel_canvas_keeps_the_panel_proportions`,
`test_panel_figure_has_no_overlapping_text`.

The `pdf` target was also re-proportioned from 8 x 6 in to 8 x 5 in: at 4:3 it
was the squarest of the three canvases, which stretched bars and panels
vertically.

## Smaller observations

- `square=True` on an 8 x 8 heatmap collapses the cells on the wide `slides`
  canvas until the annotations overlap. Figure 01 omits it and lets the cells
  fill the canvas.
- Rotated x tick labels collide inside narrow multi-panel axes; panel D of
  figure 04 uses horizontal bars instead.
- Grouped boxes need `gap=BOX_GAP` (figure 03) — seaborn otherwise draws the
  members of a hue group flush against each other.
