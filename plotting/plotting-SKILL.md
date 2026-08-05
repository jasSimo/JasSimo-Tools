---
name: plotting
description: "Use whenever creating, editing, or reviewing any data-science plot, chart, figure, or visualization intended for slides, papers, or PDF reports. Triggers on matplotlib/seaborn plotting, bar charts, heatmaps, distributions, scatter plots, or any figure that will be inserted into Google Slides, a LaTeX/manuscript paper, or a PDF. Enforces the project-wide jassimo.plotting style so every figure is colorblind-safe, presentation-sized, and free of clipping/overlap/redundancy. Do NOT use for interactive web visualizations (D3.js) or for UI/design work."
---

# Plotting mit jassimo.plotting

Alle Plots in diesem Projekt laufen über das Paket `jassimo.plotting` — die eine
Quelle der Wahrheit für Stil, Farben, Geometrie und Speichern. Dieses Skill
beschreibt, wie man es korrekt benutzt und welche Regeln unverhandelbar sind.

## Der Kern-Workflow

```python
from jassimo.plotting import set_style, new_figure, savefig, PALETTE, legend_outside

set_style("slides")                  # PFLICHT: Zielmedium zuerst festlegen
fig, ax = new_figure()               # Figur in Ziel-Geometrie (nicht plt.subplots)
ax.bar(range(5), values, color=PALETTE[0])
ax.set_title("Publication-ready title")
ax.set_xlabel("Category"); ax.set_ylabel("Value")
legend_outside(ax)                   # falls Legende nötig
savefig(fig, out_dir, "result_stem") # schreibt alle Formate des Ziels
```

Nie `plt.rcParams` direkt setzen, nie `plt.savefig` direkt aufrufen, nie
figsize/DPI/Schriftgröße/Farbe im Skript hartcodieren. Alles davon kommt aus
`jassimo.plotting`.

## Die drei Ziele — wähle bewusst

| Ziel     | Wann                                  | Ausgabe                 |
| -------- | ------------------------------------- | ----------------------- |
| `slides` | Plot geht in Google Slides (16:9)     | PNG, bei 100 % einfügen |
| `paper`  | Plot geht in LaTeX/Manuskript-Spalte  | SVG (Vektor)            |
| `pdf`    | Standalone-Ganzseiten-Figur im Report | PDF + PNG               |

Ein logischer Plot für zwei Medien → dieselbe Plot-Funktion zweimal mit
unterschiedlichem `set_style(...)` aufrufen, in getrennte Unterordner speichern.
Den Plot-Code NICHT duplizieren.

## Unverhandelbare Regeln

1. **Am Ergebnis bewerten, nicht am Code.** Nach jedem Plot die erzeugte Datei
   ansehen und aktiv prüfen: Ist die Schrift im Zielmedium präsentationsgroß?
   Wird nichts abgeschnitten? Überlappt nichts? Sind die Farben
   farbenblind-sicher? Erst dann gilt der Plot als fertig.

2. **Schriftgröße ist absolut, nicht relativ.** Die figsize ist pro Ziel fix und
   die Schriften in absoluten pt — deshalb ist die Schrift bei 5 und bei 10 Bars
   identisch groß. Niemals Schrift relativ zur Datenmenge oder Figurgröße setzen.

3. **Farben aus `PALETTE`** (Okabe–Ito, farbenblind-sicher). Der Default-Zyklus
   ist bereits gesetzt; explizite Farben ebenfalls aus `PALETTE[i]`. Keine rohen
   Hex-Codes im Plot-Skript. Projektspezifische benannte Farben in einer dünnen
   Projektschicht auf `PALETTE` aufbauen.

4. **Titel ist publikationsfertig.** Keine Entwickler-Metadaten (Run-IDs, interne
   Flags) im Titel — die gehören in den Dateinamen. Bei gefilterten Daten die
   Ausschlussrate angeben (z.B. „33% residues removed"). `n=` im Titel meint
   immer die ungefilterte Gesamtzahl.

5. **Keine Redundanz.** Jede Information erscheint an genau einer Stelle. Nicht
   dieselbe Angabe gleichzeitig in Titel, Legende und Balkenlabel.

6. **Legende außerhalb der Achse** via `legend_outside(ax)` (rechts) oder
   `legend_outside(ax, side="bottom")` (breite Multi-Panel-Figuren). Jede Farbe,
   jeder Marker, jeder Linienstil im Plot hat einen knappen Legendeneintrag
   (≤ 4 Wörter).

7. **Symmetrische Heatmaps** (M[i,j] == M[j,i]) nur als untere Dreiecksmatrix:
   `sns.heatmap(data, mask=mask_upper_triangle(data), ...)`.

8. **Alle sichtbaren Texte auf Englisch** — Titel, Achsen, Ticks, Legenden,
   Annotationen.

## Was das Paket automatisch erledigt

- Farbenblind-sicherer Default-Farbzyklus.
- `constrained_layout`: nichts wird abgeschnitten, bei identischen Pixelmaßen
  aller Figuren einer Familie.
- Automatischer Zeilenumbruch zu langer Titel.
- Speichern in allen Formaten des Ziels mit einem `savefig`-Aufruf.

## Häufige Fehler, die zu vermeiden sind

- `set_style()` vergessen → Default-Ziel `slides`, aber besser explizit setzen.
- `plt.subplots()` statt `new_figure()` → falsche Geometrie, Schrift zu klein.
- `plt.savefig()` statt `savefig()` → falsches Format, Clipping, falsche DPI.
- Slide-Plot in Slides per Maus verkleinern → Schriftgarantie verletzt.
- Denselben Plot für Paper und Slides zweimal schreiben statt zweimal rendern.
