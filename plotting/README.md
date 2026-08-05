# JasSimo-Tools/plotting

Project-agnostic, colorblind-safe plotting library for all your data-science
projects. **One** source of truth for font sizes, colors, saving rules and
target geometry — shared across any number of projects.

The core idea: every figure is rendered for **exactly one target medium**
(`slides` | `paper` | `pdf`). The target fixes geometry _and_ absolute font
sizes, so text has a **guaranteed, measured** size in the final medium — instead
of guessed point values that then turn out too small on the slide.

---

## One-time setup (SSoT across all projects)

The package lives in **one** place and is pulled into each project via an
_editable install_. "Editable" means: no copy is installed, only a reference to
this folder. Change one line here and it takes effect **immediately in all
projects** — exactly the central maintainability you want.

```bash
# In EVERY project that should use this tool, once (editable):
uv add --editable ~/code/JasSimo-Tools/plotting
```

From now on `import jassimo.plotting` is available in that project and always
points at your central file. No copying, no manual updating.

> **Rolling out changes globally:** edit `src/jassimo/plotting/style.py` in this
> repo. Done — every project uses the new version on its next run. (Only if you
> change the `__init__` exports or dependencies do you need to repeat `uv sync`
> once in the projects.)

---

## Usage

```python
from jassimo.plotting import set_style, new_figure, savefig, PALETTE, legend_outside

set_style("slides")               # once at the start of a run
fig, ax = new_figure()            # figure already in target geometry
ax.bar(range(5), values, color=PALETTE[0])
ax.set_title("My result")
ax.set_xlabel("Category"); ax.set_ylabel("Value")
legend_outside(ax)                # legend outside the axes (never overlaps)
savefig(fig, out_dir, "my_result")   # writes my_result.png (slides)
```

A plot for **both** media? Render it twice:

```python
for target in ("slides", "paper"):
    set_style(target)
    fig, ax = new_figure()
    ...                            # identical plot code
    savefig(fig, out_dir / target, "my_result")
# -> out_dir/slides/my_result.png  +  out_dir/paper/my_result.svg
```

---

## The three targets

| Target   | Geometry    | Title | Ticks | Output    | For what                                                  |
| -------- | ----------- | ----- | ----- | --------- | --------------------------------------------------------- |
| `slides` | 10 × 4.5 in | 20 pt | 15 pt | PNG       | Google Slides 16:9, insert at **100 %** (do not drag)     |
| `paper`  | 6 × 4 in    | 15 pt | 11 pt | SVG       | LaTeX/manuscript column (vector, crisp, searchable)       |
| `pdf`    | 8 × 6 in    | 17 pt | 13 pt | PDF + PNG | Standalone full-page figure                                |

**Why insert `slides` at 100 %?** The slide is internally 960 × 540 px (10 ×
5.625 in @ 96 DPI). At 100 %, 1 matplotlib-pt = 1 slide-pt, so your 20 pt title
is a clean step below the 25 pt slide title. Drag the image smaller and the font
shrinks with it — then the guarantee no longer holds.

**Why SVG for the paper and PNG for slides?** SVG is vector: crisp at any zoom
level, text stays real text. Slides occasionally render vectors incorrectly —
there PNG is more robust. PNGs can be inserted into PDFs without trouble, but
get blurry when zooming in; hence SVG for the paper.

---

## What is guaranteed

- **Font on slides always presentation-sized** — independent of the number of
  bars/data points, because the figsize is fixed and the fonts are absolute in
  pt.
- **Colorblind-safe** (Okabe–Ito) as the default color cycle — even without
  explicit color specification.
- **Nothing gets clipped** (`constrained_layout`), while at the same time all
  figures of a family have **identical pixel dimensions** (no
  `bbox_inches="tight"`).
- **Long titles** wrap automatically instead of running over the edge.
- **Legends** sit outside the axes and never overlap data.

---

## Project-specific colors/names

This library is deliberately domain-free. If a project needs named colors (e.g.
`ordered`/`disordered`), you define a **thin project layer** on top of `PALETTE`
— not in this library:

```python
# project/plotting.py
from jassimo.plotting import PALETTE
CLASS_COLORS = {"ordered": PALETTE[0], "disordered": PALETTE[3]}
```
