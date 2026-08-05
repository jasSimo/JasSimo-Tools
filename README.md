# JasSimo-Tools

Personal data-science toolkit: **one** repo, several **independently
installable** tools under the shared import namespace `jassimo`.

Each tool is a standalone package with its own dependencies. A project installs
only what it needs — a pure plotting project does not pull in the heavy
dependencies of an ML tool. Even so, they all live in one place under one
version control: change a tool (installed editable) and the change takes effect
immediately in every project that uses it. That is your SSoT.

> **Repo name vs. import name:** The repo is called `JasSimo-Tools`, the code
> imports as `jassimo` (lowercase, no hyphen — Python rule). Exactly like
> `scikit-learn` imports as `import sklearn`. That is normal.

---

## Tools

| Import             | Purpose                                                | Dependencies               |
| ------------------ | ------------------------------------------------------ | -------------------------- |
| `jassimo.plotting` | Colorblind-safe plot style, targets slides/paper/PDF    | matplotlib, seaborn, numpy |
| `jassimo.io`       | Shared data-loading helpers (placeholder, to be built out) | pandas                  |

---

## One-time setup

```bash
# 1. Clone/place the repo in a fixed location, e.g. ~/code/JasSimo-Tools
# 2. Install uv (if not already):
#    curl -LsSf https://astral.sh/uv/install.sh | sh
```

Working on the toolkit itself (all tools at once, editable):

```bash
cd ~/code/JasSimo-Tools
uv sync            # sets up .venv, installs all members editable
uv run pytest tests            # the plotting guarantees, checked on real renders
```

---

## Using it in a real project

There are two ways to pull a tool into a project. Which one you pick depends on
whether you are currently **developing** the tool or just **using** it.

### Option A — cloned locally, editable (for development)

Requires that you have cloned the repo (see above). Points at your local folder:
change a tool there and the change takes effect **immediately** in every
project. This is the right mode while you are still tinkering with the tools —
and currently your default case.

```bash
cd ~/code/my-project
uv add --editable ~/code/JasSimo-Tools/plotting      # plotting only
# uv add --editable ~/code/JasSimo-Tools/io           # additionally, if needed
```

### Option B — straight from the private repo via SSH (for using)

Clones nothing visible into your working directory — uv fetches the package from
the repo itself. Because the repo is **private**, authentication runs through
your SSH key (the same one that already makes `git clone git@github.com:...`
work). No token needed in the command.

```bash
cd ~/code/my-project
uv add "jassimo-plotting @ git+ssh://git@github.com/jasSimo/JasSimo-Tools.git#subdirectory=plotting"
```

Two things that matter here:

- **`#subdirectory=plotting`** is mandatory: because this is a multi-package
  repo, the package lives in the `plotting/` subfolder, not at the repo root.
  Without that suffix uv will not find the package. For `io` accordingly
  `#subdirectory=io`.
- This installation is **not editable** — it is a snapshot of the repo at
  install time. That is the point: a project that only uses the tool gets a
  stable version. To pull a newer version later:
  `uv lock --upgrade-package jassimo-plotting`.

> **Which option when?** While you are actively developing your tools (now):
> **Option A** everywhere, so every change takes effect immediately. **Option B**
> becomes interesting for projects that want a frozen, reproducible tool
> version — e.g. on a server or in CI/CD, where there is no local clone.

### In code

```python
from jassimo.plotting import set_style, new_figure, savefig, PALETTE

set_style("slides")
fig, ax = new_figure()
ax.bar(range(5), values, color=PALETTE[0])
ax.set_title("My result")
savefig(fig, out_dir, "my_result")
```

Details on plotting: [`plotting/README.md`](plotting/README.md).

---

## Rolling out central changes

Edit the tool in this repo (e.g. `plotting/src/jassimo/plotting/style.py`).
With **Option A** (editable) every project automatically uses the new version on
its next run — no manual updating. With **Option B** (Git URL) you deliberately
pull the change in with `uv lock --upgrade-package <package>` once you have
pushed it.

> Only if you change a tool's **dependencies** or the public API in
> `__init__.py` do you need to repeat `uv sync` / `uv add` once in the affected
> projects.

---

## Adding a new tool

Example `jassimo.bio`:

```bash
mkdir -p bio/src/jassimo/bio
# 1. bio/src/jassimo/bio/__init__.py  -> public API
# 2. bio/pyproject.toml               -> following the pattern of plotting/pyproject.toml
#    (name = "jassimo-bio", own dependencies, include = ["jassimo.bio*"])
# 3. Add "bio" to members in the root pyproject.toml.
uv sync
```

**Important:** There is deliberately NO file `src/jassimo/__init__.py`. That
absence makes `jassimo` a _namespace package_ (PEP 420) — it is the only way
several independently installable packages can share the same `jassimo`
namespace. Never create this file.

---

## Why uv?

uv manages environment and packages in one, is very fast, and with _workspaces_
has a native concept for exactly this multi-package repo (see
`[tool.uv.workspace]` in the root `pyproject.toml`). The package format itself is
standard (PEP 621) — the same packages could also be installed with pip
(`pip install -e plotting/`), should you ever need that.
