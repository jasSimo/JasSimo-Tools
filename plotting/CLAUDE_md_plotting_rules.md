<!--
  This block belongs in the CLAUDE.md of EVERY project that produces plots.
  It is deliberately short and universal — the detailed rules live in
  plotting-SKILL.md and are only loaded when needed.
-->

## Plots & visualizations

- **Every plot goes through `jassimo.plotting`** (`set_style`, `new_figure`, `savefig`,
  `PALETTE`, `legend_outside`). No local style overrides, no hardcoded font
  sizes, DPI values, figsizes or hex colors in individual plot scripts.
- **The target medium is mandatory and chosen explicitly:** `set_style("slides")`,
  `set_style("paper")` or `set_style("pdf")` as the first line of every plot run.
  No plot without a deliberate target.
- **Judge the rendered result in the target medium, not the pt value in the
  code.** After producing it, actually look at the output file and check:
  is the font presentation-sized? Is nothing clipped? Does nothing overlap? Are
  the colors colorblind-safe?
- **A logical plot exists exactly once.** If it is needed for two media, the same
  plot function is called twice with a different target — not written twice.
- **Slides are inserted at 100 %** (not scaled with the mouse), otherwise the
  font-size guarantee does not hold.
- **Colors** come from `PALETTE` (Okabe–Ito). Project-specific named colors live
  in a thin project layer on top of `PALETTE` — never hardcoded in the plot.
- **Metadata for you as the developer (run IDs and the like) do NOT belong in the
  title.** The title is publication-ready; distinguishing runs happens via the
  file name.
- **No redundancy:** a piece of information appears in exactly one place — not
  in the title, legend and bar label at the same time.
- Details on all rules: see plotting-SKILL.md.
