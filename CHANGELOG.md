# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

## [[1.3.0]](https://github.com/TVLuke/kennzeichen_buch/releases/tag/1.3) "Aachen" - 2025-07-03

### Verbessert
- Seltene Kennzeichen nutzen nun eine weitere CSV Datei um Regionsnamen zu finden, welche tatsächlich mit dem Kürzel etwas zu tun haben.

## [[1.2.9]](https://github.com/TVLuke/kennzeichen_buch/releases/tag/1.2.9) "Anhalt-Bitterfeld" - 2025-07-02

### Hinzugefügt
- SVG Bilder von Kennzeichen

## [[1.2.0]](https://github.com/TVLuke/kennzeichen_buch/releases/tag/1.2.0) "Aschaffenburg" - 2025-07-02

### Hinzugefügt
- Jetzt auch SVG Bilder von Kennzeichen

### Verbessert
- Titelbild.

### Korrigiert
- Mehr als ein München sind zu viele München. Kennzeichen konnten in mehreren Regionen vorkommen, und dann wurden auch mehrere Punkte aufs Titelbild gesetzt.

## [[1.1.0]](https://github.com/TVLuke/kennzeichen_buch/releases/tag/1.1.0) "Aalen Ostalbkreis" - 2025-07-01

### Hinzugefügt
- Regionsspezifische Titelbilder für jedes Kennzeichen
  - Roter Punkt markiert die Region auf der Karte
  - Text "<Region> Edition" am unteren Bildrand
  - Autorenzeile "von Lukas Ruge" unter dem Editionstext
- Versionshinweis im Lizenzabschnitt des Buches

### Verbessert
- Integration der Titelbildgenerierung in den Batch-Prozess
- Automatische Erkennung und Verwendung regionsspezifischer Titelbilder
- Titelbilder werden in die PDF-Datei eingefügt. Qualität besser.

### Korrigiert
- Fehler bei der Berechnung der Distanz zwischen Orten korrigiert
- Falsche Annahme: Ein kennzeichen kann nur ein mal auftauchen. Das stimmt aber nicht weil "Erste Verordnung zur Änderung der Fahrzeug-Zulassungsverordnung und anderer straßenverkehrsrechtlicher Vorschriften"

## [[1.0]](https://github.com/TVLuke/kennzeichen_buch/releases/tag/1.0) "Augsburg" - 2025-06-30

### Hinzugefügt
- Erste vollständige Version des KFZ-Kennzeichen Sammelbuchs
- Drei verschiedene Rätseltypen
- Möglichkeit, über Konfiguration das Home-Kennzeichen zu setzen
- Automatische Generierung von Büchern für alle Kennzeichen
- PDF-Ausgabe mit Titelseite, Karten und Rätseln
