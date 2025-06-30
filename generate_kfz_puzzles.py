#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os

# Liste von verkehrsbezogenen Nomen für Kinder
VERKEHRS_WOERTER = [
    "AMPEL", "AUTO", "ZEBRASTREIFEN", "STRASSE", "FAHRRAD", "FUSSGAENGER", 
    "KREUZUNG", "AUTOBAHN", "BAHNHOF", "BRUECKE", "TUNNEL", "PARKPLATZ", 
    "TANKSTELLE", "BUSHALTESTELLE", "STRASSENBAHN", "MOTORRAD", "LASTWAGEN", 
    "POLIZEIAUTO", "FEUERWEHR", "KRANKENWAGEN", "VERKEHRSSCHILD", "BAUSTELLE",
    "RADWEG", "FUSSGAENGERZONE", "KREISVERKEHR", "UNTERFUEHRUNG", "UEBERFUEHRUNG",
    "FAHRBAHNMARKIERUNG", "LEITPLANKE", "VERKEHRSINSEL", "STRASSENLATERNE",
    "BLINKLICHT", "NEBELSCHEINWERFER", "AUTOSITZ", "KINDERSITZ", "SICHERHEITSGURT",
    "FAHRRADHELM", "WARNWESTE", "VERKEHRSAMPEL", "STOPPSCHILD", "VORFAHRTSSCHILD",
    "GESCHWINDIGKEITSBEGRENZUNG", "AUTOBAHNAUSFAHRT", "AUTOBAHNAUFFAHRT", 
    "RASTPLATZ", "RASTSTAETTE", "MAUTSTELLE", "FAHRSCHULE", "FUEHRERSCHEIN",
    "VERKEHRSREGELN", "VERKEHRSERZIEHUNG", "SCHULWEG", "SCHULBUS", "FAHRRADSTAENDER",
    "FAHRRADSCHLOSS", "FAHRRADKLINGEL", "FAHRRADKORB", "FAHRRADLICHT", "REFLEKTOREN",
    "STRASSENVERKEHR", "FUSSGAENGERAMPEL", "VERKEHRSUEBERWACHUNG", "BLITZANLAGE",
    "VERKEHRSKONTROLLE", "FAHRZEUGPAPIERE", "AUTOKENNZEICHEN", "NUMMERNSCHILD",
    "FAHRTRICHTUNG", "EINBAHNSTRASSE", "GEGENVERKEHR", "UEBERHOLVERBOT",
    "PARKVERBOT", "HALTEVERBOT", "PARKSCHEIBE", "PARKUHR", "PARKKRALLE",
    "ABSCHLEPPWAGEN", "WERKSTATT", "REIFENWECHSEL", "WINTERREIFEN", "SOMMERREIFEN",
    "SCHNEEKETTEN", "WARNDREIECK", "VERBANDSKASTEN", "FEUERLOESCHER", "WAGENHEBER",
    "RESERVERAD", "AUTOSCHLUESSEL", "ZUENDSCHLUESSEL", "FERNBEDIENUNG", "AUTOTUER",
    "KOFFERRAUM", "MOTORHAUBE", "WINDSCHUTZSCHEIBE", "SCHEIBENWISCHER", "SEITENSPIEGEL",
    "RUECKSPIEGEL", "BLINKER", "SCHEINWERFER", "RUECKLICHT", "BREMSLICHT", "NEBELSCHLUSSLEUCHTE",
    "STOSSSTANGE", "AUSPUFF", "KATALYSATOR", "KRAFTSTOFFTANK", "BENZIN", "DIESEL",
    "ELEKTROAUTO", "HYBRIDAUTO", "LADESTELLE", "STECKDOSE", "BATTERIE", "LADESTATION"
]

def generate_kfz_puzzles(regular_codes, code_to_name):
    """
    Generiert Rätsel, bei denen Wörter aus KFZ-Kennzeichen gebildet werden.
    
    Args:
        regular_codes: Liste der regulären KFZ-Kennzeichen
        code_to_name: Dictionary, das KFZ-Kennzeichen auf Regionsnamen abbildet
    
    Returns:
        Eine Liste von Rätseln im Format:
        {
            "wort": "FAHRRAD",
            "loesung": [
                {"code": "F", "name": "Frankfurt am Main"},
                {"code": "A", "name": "Augsburg"},
                {"code": "H", "name": "Hannover"},
                {"code": "R", "name": "Regensburg"},
                {"code": "RA", "name": "Rastatt"},
                {"code": "D", "name": "Düsseldorf"}
            ]
        }
    """
    puzzles = []
    
    # Erstelle ein Set mit allen Kennzeichen für schnellere Suche
    code_set = set(regular_codes)
    
    # Erstelle ein Dictionary mit allen möglichen Präfixen
    # z.B. für "AB" sind die Präfixe "A" und "AB"
    code_prefixes = {}
    for code in regular_codes:
        for i in range(1, len(code) + 1):
            prefix = code[:i]
            if prefix not in code_prefixes:
                code_prefixes[prefix] = []
            code_prefixes[prefix].append(code)
    
    # Filtere Wörter mit mindestens 7 Zeichen
    filtered_words = [word for word in VERKEHRS_WOERTER if len(word) >= 7]
    print(f"Verarbeite {len(filtered_words)} Wörter mit mindestens 7 Zeichen...")
    
    for word_index, wort in enumerate(filtered_words):
        if word_index % 10 == 0:
            print(f"Fortschritt: {word_index}/{len(filtered_words)} Wörter verarbeitet")
            
        # Dynamische Programmierung: Speichere die beste Lösung für jedes Teilwort
        # dp[i] = beste Lösung für das Teilwort wort[i:]
        n = len(wort)
        dp = [None] * (n + 1)
        dp[n] = []  # Leere Liste für das leere Suffix
        
        # Fülle die DP-Tabelle von hinten nach vorne
        for i in range(n - 1, -1, -1):
            best_solution = None
            min_codes = float('inf')
            
            # Probiere alle möglichen Kennzeichen, die mit dem aktuellen Teilwort beginnen
            for j in range(i + 1, min(i + 4, n + 1)):  # Maximal 3 Zeichen pro Kennzeichen
                prefix = wort[i:j]
                if prefix in code_set and dp[j] is not None:
                    solution = [prefix] + dp[j]
                    if len(solution) < min_codes:
                        min_codes = len(solution)
                        best_solution = solution
            
            dp[i] = best_solution
        
        # Wenn eine Lösung gefunden wurde und sie mindestens 3 Kennzeichen verwendet
        if dp[0] and len(dp[0]) >= 3:
            puzzle = {
                "wort": wort,
                "loesung": [{"code": code, "name": code_to_name.get(code, "Unbekannt")} for code in dp[0]]
            }
            puzzles.append(puzzle)
    
    return puzzles

def save_puzzles_to_json(puzzles, output_file="kfz_puzzles.json"):
    """
    Speichert die generierten Rätsel in einer JSON-Datei.
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(puzzles, f, ensure_ascii=False, indent=4)
    
    print(f"{len(puzzles)} Rätsel wurden in '{output_file}' gespeichert.")

def main(regular_codes=None, code_to_name=None):
    """
    Hauptfunktion zum Generieren der KFZ-Kennzeichen-Rätsel.
    Kann entweder direkt aufgerufen werden oder aus dem Hauptskript.
    """
    if regular_codes is None or code_to_name is None:
        # Wenn die Funktion direkt aufgerufen wird, importiere die Daten aus dem Hauptskript
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from generate_kfz_maps_neu import extract_kfz_codes, load_shapefile
            
            # Lade die Shapefile-Daten
            shapefile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vg250_krs.shp")
            gdf = load_shapefile(shapefile_path)
            
            # Extrahiere die KFZ-Kennzeichen
            regular_codes, _, _, code_to_name, _, _ = extract_kfz_codes(gdf)
            
            print(f"Daten erfolgreich geladen: {len(regular_codes)} reguläre Kennzeichen gefunden.")
        except Exception as e:
            print(f"Fehler beim Laden der KFZ-Daten: {e}")
            return
    
    puzzles = generate_kfz_puzzles(regular_codes, code_to_name)
    save_puzzles_to_json(puzzles)
    
    # Gib einige Beispielrätsel aus
    print("\nBeispiele für generierte Rätsel:")
    for i, puzzle in enumerate(puzzles[:5], 1):
        codes = [item["code"] for item in puzzle["loesung"]]
        names = [item["name"] for item in puzzle["loesung"]]
        print(f"{i}. Wort: {puzzle['wort']}")
        print(f"   Lösung: {' - '.join(names)} ({'-'.join(codes)})")
        print()
    
    return puzzles

if __name__ == "__main__":
    main()
