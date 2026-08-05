<!--
  Dieser Block gehört in die CLAUDE.md JEDES Projekts, das Plots erzeugt.
  Er ist bewusst kurz und universell — die ausführlichen Regeln stehen im
  Plotting-SKILL.md und werden nur bei Bedarf geladen.
-->

## Plots & Visualisierungen

- **Jeder Plot läuft über `jassimo.plotting`** (`set_style`, `new_figure`, `savefig`,
  `PALETTE`, `legend_outside`). Keine lokalen Style-Overrides, keine hartcodierten
  Schriftgrößen, DPI-Werte, figsizes oder Hex-Farben in einzelnen Plot-Skripten.
- **Zielmedium ist Pflicht und wird explizit gewählt:** `set_style("slides")`,
  `set_style("paper")` oder `set_style("pdf")` als erste Zeile jedes Plot-Runs.
  Ohne bewusstes Ziel kein Plot.
- **Bewertet wird am gerenderten Ergebnis im Zielmedium, nicht am pt-Wert im
  Code.** Nach dem Erzeugen die Ausgabedatei tatsächlich ansehen und prüfen:
  Schrift präsentationsgroß? Nichts abgeschnitten? Nichts überlappt? Farben
  farbenblind-sicher?
- **Ein logischer Plot existiert genau einmal.** Wird er für zwei Medien
  gebraucht, wird dieselbe Plot-Funktion zweimal mit unterschiedlichem Ziel
  aufgerufen — nicht zweimal geschrieben.
- **Slides werden bei 100 % eingefügt** (nicht per Maus skaliert), sonst greift
  die Schriftgrößen-Garantie nicht.
- **Farben** kommen aus `PALETTE` (Okabe–Ito). Projektspezifische benannte Farben
  leben in einer dünnen Projektschicht, die auf `PALETTE` aufsetzt — nie durch
  Hardcoding im Plot.
- **Metadaten für dich als Entwickler (Run-IDs o.ä.) gehören NICHT in den Titel.**
  Der Titel ist publikationsfertig; Run-Unterscheidung läuft über den Dateinamen.
- **Keine Redundanz:** eine Information erscheint an genau einer Stelle — nicht
  gleichzeitig in Titel, Legende und Balkenbeschriftung.
- Details zu allen Regeln: siehe Plotting-SKILL.md.
