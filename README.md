# JasSimo-Tools

Persönliches Data-Science-Toolkit: **ein** Repo, mehrere **getrennt
installierbare** Werkzeuge unter dem gemeinsamen Import-Namespace `jassimo`.

Jedes Werkzeug ist ein eigenständiges Paket mit eigenen Abhängigkeiten. Ein
Projekt installiert nur, was es braucht — ein reines Plot-Projekt zieht nicht die
schweren Abhängigkeiten eines ML-Werkzeugs mit. Trotzdem leben alle an einem Ort
unter einer Versionskontrolle: Änderst du ein Werkzeug (editable installiert),
wirkt die Änderung sofort in allen Projekten, die es nutzen. Das ist deine SSoT.

> **Repo-Name vs. Import-Name:** Das Repo heißt `JasSimo-Tools`, der Code
> importiert sich als `jassimo` (klein, ohne Bindestrich — Python-Regel). Genau
> wie `scikit-learn` sich als `import sklearn` importiert. Das ist normal.

---

## Werkzeuge

| Import             | Zweck                                                    | Abhängigkeiten             |
| ------------------ | -------------------------------------------------------- | -------------------------- |
| `jassimo.plotting` | Farbenblind-sicherer Plot-Stil, Ziele Slides/Paper/PDF   | matplotlib, seaborn, numpy |
| `jassimo.io`       | Geteilte Daten-Lade-Helfer (Platzhalter, wird ausgebaut) | pandas                     |

---

## Einmalige Einrichtung

```bash
# 1. Repo an einen festen Ort klonen/legen, z.B. ~/code/JasSimo-Tools
# 2. uv installieren (falls noch nicht):
#    curl -LsSf https://astral.sh/uv/install.sh | sh
```

Am Toolkit selbst arbeiten (alle Werkzeuge auf einmal, editable):

```bash
cd ~/code/JasSimo-Tools
uv sync            # richtet .venv ein, installiert alle Mitglieder editable
```

---

## In einem echten Projekt nutzen

Es gibt zwei Wege, ein Werkzeug in ein Projekt einzubinden. Welchen du nimmst,
hängt davon ab, ob du das Werkzeug gerade **weiterentwickelst** oder nur
**benutzt**.

### Variante A — lokal geklont, editable (zum Entwickeln)

Setzt voraus, dass du das Repo geklont hast (siehe oben). Zeigt auf deinen
lokalen Ordner: Änderst du dort ein Werkzeug, wirkt die Änderung **sofort** in
allen Projekten. Das ist der richtige Modus, solange du an den Tools schraubst —
und aktuell dein Standardfall.

```bash
cd ~/code/mein-projekt
uv add --editable ~/code/JasSimo-Tools/plotting      # nur Plotting
# uv add --editable ~/code/JasSimo-Tools/io           # bei Bedarf zusätzlich
```

### Variante B — direkt aus dem privaten Repo per SSH (zum Benutzen)

Klont nichts sichtbar in dein Arbeitsverzeichnis — uv holt das Paket selbst aus
dem Repo. Weil das Repo **privat** ist, läuft die Authentifizierung über deinen
SSH-Schlüssel (denselben, mit dem `git clone git@github.com:...` schon
funktioniert). Kein Token im Befehl nötig.

```bash
cd ~/code/mein-projekt
uv add "jassimo-plotting @ git+ssh://git@github.com/jasSimo/JasSimo-Tools.git#subdirectory=plotting"
```

Zwei Dinge, die hier wichtig sind:

- **`#subdirectory=plotting`** ist Pflicht: Weil dies ein Multi-Paket-Repo ist,
  liegt das Paket im Unterordner `plotting/`, nicht in der Repo-Wurzel. Ohne den
  Zusatz findet uv das Paket nicht. Für `io` entsprechend `#subdirectory=io`.
- Diese Installation ist **nicht editable** — sie ist eine Momentaufnahme des
  Repos zum Installationszeitpunkt. Das ist der Sinn: ein Projekt, das das Tool
  nur benutzt, bekommt eine stabile Version. Um später eine neuere Version zu
  ziehen: `uv lock --upgrade-package jassimo-plotting`.

> **Wann welche Variante?** Solange du deine Tools aktiv entwickelst (jetzt):
> überall **Variante A**, damit jede Änderung sofort greift. **Variante B** wird
> interessant für Projekte, die eine eingefrorene, reproduzierbare Tool-Version
> wollen — z.B. auf einem Server oder in CI/CD, wo kein lokaler Klon liegt.

### Im Code

```python
from jassimo.plotting import set_style, new_figure, savefig, PALETTE

set_style("slides")
fig, ax = new_figure()
ax.bar(range(5), values, color=PALETTE[0])
ax.set_title("My result")
savefig(fig, out_dir, "my_result")
```

Details zum Plotting: [`plotting/README.md`](plotting/README.md).

---

## Zentrale Änderungen ausrollen

Editier das Werkzeug in diesem Repo (z.B. `plotting/src/jassimo/plotting/style.py`).
Bei **Variante A** (editable) nutzt jedes Projekt beim nächsten Lauf automatisch
die neue Version — kein Nachziehen von Hand. Bei **Variante B** (Git-URL) ziehst
du die Änderung bewusst mit `uv lock --upgrade-package <paket>` nach, sobald du
sie gepusht hast.

> Nur wenn du **Abhängigkeiten** eines Werkzeugs änderst oder die öffentliche API
> in `__init__.py`, in den betroffenen Projekten einmal `uv sync` / `uv add`
> wiederholen.

---

## Neues Werkzeug hinzufügen

Beispiel `jassimo.bio`:

```bash
mkdir -p bio/src/jassimo/bio
# 1. bio/src/jassimo/bio/__init__.py  -> öffentliche API
# 2. bio/pyproject.toml               -> nach dem Muster von plotting/pyproject.toml
#    (name = "jassimo-bio", eigene dependencies, include = ["jassimo.bio*"])
# 3. In der Wurzel-pyproject.toml "bio" zu members hinzufügen.
uv sync
```

**Wichtig:** Es gibt bewusst KEINE Datei `src/jassimo/__init__.py`. Dieses Fehlen
macht `jassimo` zu einem _Namespace-Package_ (PEP 420) — nur so können mehrere
getrennt installierbare Pakete denselben `jassimo`-Namespace teilen. Lege diese
Datei niemals an.

---

## Warum uv?

uv verwaltet Environment und Pakete in einem, ist sehr schnell, und hat mit
_Workspaces_ ein natives Konzept für genau dieses Multi-Paket-Repo (siehe
`[tool.uv.workspace]` in der Wurzel-`pyproject.toml`). Das Paketformat selbst ist
Standard (PEP 621) — dieselben Pakete ließen sich auch mit pip installieren
(`pip install -e plotting/`), falls du das je brauchst.
