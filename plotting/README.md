# JasSimo-Tools/plotting

Projekt-agnostische, farbenblind-sichere Plot-Bibliothek für alle deine
Data-Science-Projekte. **Eine** Quelle der Wahrheit für Schriftgrößen, Farben,
Speicherregeln und Ziel-Geometrie — geteilt über beliebig viele Projekte.

Der Kern-Gedanke: Jede Figur wird für **genau ein Zielmedium** gerendert
(`slides` | `paper` | `pdf`). Das Ziel legt Geometrie _und_ absolute
Schriftgrößen fest, sodass Text im Endmedium eine **garantierte, gemessene**
Größe hat — statt geratener Punktwerte, die auf der Slide dann zu klein sind.

---

## Einmalige Einrichtung (SSoT über alle Projekte)

Das Paket lebt an **einem** Ort und wird per _editable install_ in jedes Projekt
eingebunden. „Editable" heißt: Es wird keine Kopie installiert, sondern ein
Verweis auf diesen Ordner. Änderst du hier eine Zeile, wirkt sie **sofort in
allen Projekten** — genau die zentrale Wartbarkeit, die du willst.

```bash
# In JEDEM Projekt, das dieses Werkzeug nutzen soll, einmalig (editable):
uv add --editable ~/code/JasSimo-Tools/plotting
```

Ab jetzt ist `import jassimo.plotting` in diesem Projekt verfügbar und zeigt immer auf
deine zentrale Datei. Kein Kopieren, kein Nachziehen von Hand.

> **Änderungen global ausrollen:** editiere `src/jassimo/plotting/style.py` in diesem
> Repo. Fertig — jedes Projekt nutzt beim nächsten Lauf die neue Version. (Nur
> wenn du die `__init__`-Exporte oder Abhängigkeiten änderst, in den Projekten
> einmal `uv sync` wiederholen.)

---

## Nutzung

```python
from jassimo.plotting import set_style, new_figure, savefig, PALETTE, legend_outside

set_style("slides")               # 1x am Anfang eines Runs
fig, ax = new_figure()            # Figur schon in Ziel-Geometrie
ax.bar(range(5), values, color=PALETTE[0])
ax.set_title("My result")
ax.set_xlabel("Category"); ax.set_ylabel("Value")
legend_outside(ax)                # Legende außerhalb der Achse (überlappt nie)
savefig(fig, out_dir, "my_result")   # schreibt my_result.png (slides)
```

Einen Plot für **beide** Medien? Zweimal rendern:

```python
for target in ("slides", "paper"):
    set_style(target)
    fig, ax = new_figure()
    ...                            # identischer Plot-Code
    savefig(fig, out_dir / target, "my_result")
# -> out_dir/slides/my_result.png  +  out_dir/paper/my_result.svg
```

---

## Die drei Ziele

| Ziel     | Geometrie   | Titel | Ticks | Ausgabe   | Wofür                                                     |
| -------- | ----------- | ----- | ----- | --------- | --------------------------------------------------------- |
| `slides` | 10 × 4.5 in | 20 pt | 15 pt | PNG       | Google Slides 16:9, bei **100 %** einfügen (nicht ziehen) |
| `paper`  | 6 × 4 in    | 15 pt | 11 pt | SVG       | LaTeX/Manuskript-Spalte (Vektor, scharf, durchsuchbar)    |
| `pdf`    | 8 × 6 in    | 17 pt | 13 pt | PDF + PNG | Standalone-Ganzseiten-Figur                               |

**Warum `slides` bei 100 % einfügen?** Die Slide ist intern 960 × 540 px (10 ×
5.625 in @ 96 DPI). Bei 100 % ist 1 matplotlib-pt = 1 Slide-pt, dein 20-pt-Titel
also eine saubere Stufe unter dem 25-pt-Slide-Titel. Ziehst du das Bild kleiner,
schrumpft auch die Schrift — dann greift die Garantie nicht mehr.

**Warum SVG fürs Paper und PNG für Slides?** SVG ist Vektor: bei jeder Zoomstufe
scharf, Text bleibt echter Text. Slides rendern Vektoren gelegentlich fehlerhaft
— dort ist PNG robuster. PNGs lassen sich problemlos in PDFs einfügen, sind aber
beim Reinzoomen unscharf; fürs Paper daher SVG.

---

## Was garantiert erfüllt ist

- **Schrift auf Slides immer präsentationsgroß** — unabhängig von der Anzahl der
  Bars/Datenpunkte, weil die figsize fix ist und die Schriften absolut in pt.
- **Farbenblind-sicher** (Okabe–Ito) als Default-Farbzyklus — auch ohne
  explizite Farbangabe.
- **Nichts wird abgeschnitten** (`constrained_layout`), bei zugleich **identischen
  Pixelmaßen** aller Figuren einer Familie (kein `bbox_inches="tight"`).
- **Lange Titel** brechen automatisch um statt über den Rand zu laufen.
- **Legenden** liegen außerhalb der Achse und überlappen nie Daten.

---

## Projektspezifische Farben/Namen

Diese Bibliothek ist bewusst domänenfrei. Braucht ein Projekt benannte Farben
(z.B. `ordered`/`disordered`), definierst du eine **dünne Projektschicht**, die
auf `PALETTE` aufsetzt — nicht in dieser Bibliothek:

```python
# projekt/plotting.py
from jassimo.plotting import PALETTE
CLASS_COLORS = {"ordered": PALETTE[0], "disordered": PALETTE[3]}
```
