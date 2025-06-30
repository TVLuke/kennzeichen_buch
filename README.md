# Mein großes Kennzeichen Buch

Ein Sammelbuch für deutsche Autokennzeichen mit Karten und Checklisten. Zielgruppe sind vermutlich Kinder im Alter von sechs oder sieben Jahren, da entsheht anscheinend ja häufiger mal eine Faszination für Autkennzeichen. Das Buch enthält einfache Rätsel und kurze Texte und hilft beim erkennen von Buchstaben und Lesenlernen.

## Beschreibung

Dieses Projekt erstellt ein PDF-Sammelbuch für deutsche KFZ-Kennzeichen. Das Buch enthält:

- Eine Titelseite mit einer Wortwolke der Regionen
- Karten von Deutschland, die die Regionen der Kennzeichen farblich hervorheben
- Listen mit Checkboxen für alle regulären und seltenen Kennzeichen
- Lizenzinformationen und Quellenangaben

Das Buch ist so gestaltet, dass es ausgedruckt und gebunden werden kann. Die Seitenzahl ist immer durch 4 teilbar, und es gibt mindestens eine leere Seite am Ende, was für den Druck optimal ist.

## Voraussetzungen

- Python 3.6 oder höher
- Eine virtuelle Python-Umgebung (z.B. `kfz_env`)
- LaTeX-Installation (pdflatex muss im PATH verfügbar sein)

### Python-Abhängigkeiten

- pandas
- geopandas
- fiona
- matplotlib
- numpy
- shapely
- PyPDF2
- Pillow
- wordcloud

## Installation

1. Klonen Sie das Repository:
   ```
   git clone https://github.com/yourusername/kfz-kennzeichen-buch.git
   cd kfz-kennzeichen-buch
   ```

2. Erstellen Sie eine virtuelle Umgebung und installieren Sie die Abhängigkeiten:
   ```
   python -m venv kfz_env
   source kfz_env/bin/activate  # Unter Windows: kfz_env\Scripts\activate
   pip install pandas geopandas fiona matplotlib numpy shapely PyPDF2 Pillow wordcloud
   ```

## Verwendung

Führen Sie einfach das Hauptskript aus:

```
python main.py
```

Dies führt folgende Schritte aus:
1. Erstellt das Titelbild mit einer Wortwolke der Regionen
2. Generiert Karten für alle regulären Kennzeichen
3. Erstellt ein LaTeX-Dokument mit Listen aller Kennzeichen
4. Kompiliert das LaTeX-Dokument zu einem PDF
5. Fügt das Titelbild und leere Seiten hinzu, um ein druckfertiges PDF zu erstellen

Das fertige PDF wird als `kfz_sammelbuch_final.pdf` gespeichert.

## Einzelne Komponenten

- `main.py`: Hauptskript, das den gesamten Prozess steuert
- `create_title_image.py`: Erstellt das Titelbild mit einer Wortwolke
- `generate_kfz_maps_neu.py`: Generiert die Karten und das LaTeX-Dokument

## Datenquellen

Das Projekt verwendet zwei Hauptdatenquellen:

1. **KfzKennzeichen-Repository**  
   Quelle: https://github.com/Octoate/KfzKennzeichen/  
   Copyright © 2014 Tim Riemann  
   Lizenz: MIT Lizenz

2. **Verwaltungsgrenzen der Bundesrepublik Deutschland**  
   Quelle: https://mis.bkg.bund.de/trefferanzeige?docuuid=D7BCF56C-ECDF-4672-9C19-8C668C67E378  
   Lizenz: Datenlizenz Deutschland Namensnennung 2.0 (https://www.govdata.de/dl-de/by-2-0)  
   Herausgeber: Bundesamt für Kartographie und Geodäsie

## Lizenz

### Code (Python-Skripte)
Die Python-Skripte in diesem Projekt stehen unter der **MIT-Lizenz**.

```
MIT License

Copyright (c) 2025 Lukas Ruge

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

### Inhalte (PDF und Bilder in output_maps)
Das generierte PDF und die Bilder im Verzeichnis `output_maps` stehen unter der **Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)**.

```
Creative Commons Attribution-NonCommercial 4.0 International License

Copyright (c) 2025 Lukas Ruge

Diese Inhalte dürfen geteilt und adaptiert werden unter folgenden Bedingungen:
- Namensnennung: Sie müssen angemessene Urheber- und Rechteangaben machen.
- Nicht kommerziell: Sie dürfen das Material nicht für kommerzielle Zwecke nutzen.

Vollständiger Lizenztext: https://creativecommons.org/licenses/by-nc/4.0/legalcode
```

## Note on Use of LLMs

This code was created using, among other tools, LLM tools.

## Autor

Lukas Ruge © 2025
